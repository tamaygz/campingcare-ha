import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import websocket_api
from homeassistant.helpers.event import async_call_later  # Import async_call_later directly
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, CONF_API_KEY, CONF_API_URL, CONF_NAME
from .api import CampingCareAPI


from aiohttp import ClientError, ClientConnectionError, ClientSession, InvalidURL, web, web_response
from aiohttp.web_exceptions import HTTPBadRequest

_LOGGER = logging.getLogger(__name__)

class CampingCarePlaceSensor(Entity):
    """Representation of a CampingCare Place Sensor."""

    def __init__(self, hass, api_client, place):
        self.hass = hass
        self.api_client = api_client
        self.place = place
        self._name = f"Place {place['id']}"
        self._state = None
        self._attributes = {
            "reservation_id": place.get("reservation_id"),
            "license_plate": place.get("license_plate"),
            "customer": place.get("customer"),
        }

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            place_data = await self.api_client.get_place(self.place['id'])
            self._state = place_data.get("in_use", False)
            self._attributes.update({
                "reservation_id": place_data.get("reservation_id"),
                "license_plate": place_data.get("license_plate"),
                "customer": place_data.get("customer"),
            })
        except Exception as e:
            _LOGGER.error("Failed to update place sensor: %s", e)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the CampingCare integration."""
    _LOGGER.info("CampingCareHA: async_setup called — skipping YAML config.")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up CampingCareHA from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Use updated values from options if available
    api_key = entry.options.get(CONF_API_KEY, entry.data[CONF_API_KEY])
    api_url = entry.options.get(CONF_API_URL, entry.data[CONF_API_URL])
    name = entry.options.get(CONF_NAME, entry.data[CONF_NAME])

    _LOGGER.info("Setting up CampingCareHA for '%s'", name)

    # Initialize the API client
    api_client = CampingCareAPI(api_url, api_key)

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NAME: name,
        "api_client": api_client,
    }

    # Test the API connection
    if not await api_client.test_connection():
        _LOGGER.error("CampingCareHA: Failed to connect to the CampingCare API.")
        return False

    websocket_api.async_register_command(
        hass,
        websocket_query_license_plate,
        f"{DOMAIN}/query_license_plate"
    )

    # Fetch translations for error messages
    translations = await async_get_translations(hass, "en", "component")

    async def handle_check_plate(call: ServiceCall):
        """Handle the check_plate service."""
        plate = call.data.get("plate")
        entry_id = list(hass.data[DOMAIN].keys())[0] if hass.data[DOMAIN] else None

        if not entry_id:
            _LOGGER.error(translations["errors.api_connection_failed"])
            return

        api_client = hass.data[DOMAIN][entry_id]["api_client"]
        result = await api_client.check_license_plate(plate)

        if result["success"]:
            _LOGGER.info(translations["service.query_plate.description"], plate, result["data"])
        else:
            _LOGGER.warning(translations["errors.invalid_license_plate"], plate, result["error"])
    
    async def handle_query_plate(call: ServiceCall):
        """Handle the query_plate service."""
        plate = call.data.get("plate")
        entry_id = list(hass.data[DOMAIN].keys())[0] if hass.data[DOMAIN] else None

        if not entry_id:
            _LOGGER.error(translations["errors.api_connection_failed"])
            return

        api_client = hass.data[DOMAIN][entry_id]["api_client"]
        start_date = call.data.get("start_date")
        end_date = call.data.get("end_date")
        result = await api_client.query_license_plate(plate, start_date=start_date, end_date=end_date)

        if result["success"]:
            hass.bus.async_fire(
                f"{DOMAIN}_query_license_plate",
                {
                    "entry_id": entry_id,
                    "plate": plate,
                    "result": result["data"],
                }
            )
            _LOGGER.info(translations["websocket.query_license_plate.description"], plate)
        else:
            _LOGGER.warning(translations["errors.api_request_failed"], plate, result["error"])
    
    async def handle_get_reservation(call: ServiceCall):
        """Handle the get_reservation service."""
        reservation_id = call.data.get("reservation_id")
        entry_id = list(hass.data[DOMAIN].keys())[0] if hass.data[DOMAIN] else None
    
        if not entry_id:
            _LOGGER.error(translations["errors.api_connection_failed"])
            return
    
        api_client = hass.data[DOMAIN][entry_id]["api_client"]
        result = await api_client.get_reservation(reservation_id)
    
        if result["success"]:
            hass.bus.async_fire(
                f"{DOMAIN}_get_reservation",
                {
                    "entry_id": entry_id,
                    "reservation_id": reservation_id,
                    "result": result["data"],
                }
            )
            _LOGGER.info(translations["service.query_plate.description"], reservation_id, result["data"])
        else:
            _LOGGER.warning(translations["errors.api_request_failed"], reservation_id, result["error"])

    # Register the services for this specific instance
    hass.services.async_register(
        domain=DOMAIN,
        service=f"{entry.entry_id}_get_reservation",
        service_func=handle_get_reservation,
        schema=vol.Schema({
            vol.Required("reservation_id"): str,
        }),
    )

    hass.services.async_register(
        domain=DOMAIN,
        service=f"{entry.entry_id}_check_plate",
        service_func=handle_check_plate,
        schema=vol.Schema({
            vol.Required("plate"): str,
        }),
    )

    hass.services.async_register(
        domain=DOMAIN,
        service=f"{entry.entry_id}_query_plate",
        service_func=handle_query_plate,
        schema=vol.Schema({
            vol.Required("plate"): str,
            vol.Optional("start_date"): str,
            vol.Optional("end_date"): str,
        }),
    )

    # Fetch places and create sensors
    places = await api_client.get_places()
    for place in places:
        sensor = CampingCarePlaceSensor(hass, api_client, place)
        hass.helpers.entity_platform.async_add_entities([sensor])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.info("Unloaded CampingCareHA entry '%s'", entry.entry_id)
    return True

async def websocket_query_license_plate(hass: HomeAssistant, connection, msg):
    """Handle WebSocket license plate lookup."""
    plate = msg.get("plate")
    entry_id = msg.get("entry_id")

    # Log the entry_id for debugging
    _LOGGER.debug("CampingCareHA: config entry id: %s", entry_id)
    _LOGGER.debug("CampingCareHA: WebSocket query_license_plate called with plate: %s", plate)

    if not plate or not entry_id or entry_id not in hass.data[DOMAIN]:
        if connection:
            connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, translations["websocket.query_license_plate.error.missing_plate"])
        return

    # Retrieve the API client
    api_client = hass.data[DOMAIN][entry_id]["api_client"]

    # Use the API client to check the license plate
    result = await api_client.check_license_plate(plate)

    if result["success"]:
        _LOGGER.debug("CampingCareHA: License plate %s is valid: %s", plate, result["data"])
        if connection:
            connection.send_message({
                "id": msg["id"],
                "type": "result",
                "success": True,
                "result": result["data"]
            })
    else:
        _LOGGER.error("CampingCareHA: License plate %s check failed: %s", plate, result["error"])
        if connection:
            connection.send_error(msg["id"], "api_error", result["error"])
            
# async def test_api_connection(url: str, api_key: str):
#     """Test the API connection."""
#     try:
#         async with ClientSession() as session:
#             async with session.get(f"{url}/version", headers={"Authorization": f"Bearer {api_key}"}) as response:
#                 if response.status == 200:
#                     _LOGGER.debug("CampingCareHA: API test successful.")
#                     return True
#                 _LOGGER.warning("CampingCareHA: API test returned status %s", response.status)
#     except ClientError as e:
#         _LOGGER.error("CampingCareHA: API test failed: %s", e)
#     return False

# async def websocket_query_license_plate(hass: HomeAssistant, connection, msg):
#     """Handle WebSocket license plate lookup."""
#     plate = msg.get("plate")
#     entry_id = msg.get("entry_id")
    
#     # Log the entry_id for debugging
#     _LOGGER.debug("CampingCareHA: config entry id: %s", entry_id)
#     _LOGGER.debug("CampingCareHA: WebSocket query_license_plate called with plate: %s", plate)

#     if not plate or not entry_id or entry_id not in hass.data[DOMAIN]:
#         if connection:
#             connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Missing or invalid plate/entry_id")
#         return

#     config = hass.data[DOMAIN][entry_id]
#     url = config[CONF_API_URL]
#     api_key = config[CONF_API_KEY]
#     _LOGGER.debug("CampingCareHA: trying on %s with key %s ", url, api_key)

#     try:
#         async with ClientSession() as session:
#             async with session.get(
#                 f"{url}/license_plates/check_plate?plate={plate}",
#                 headers={"Authorization": f"Bearer {api_key}"}
#             ) as response:
#                 _LOGGER.debug("CampingCareHA: response: %s", response)
                
#                 if response.status == 200:
#                     data = await response.json()
#                     _LOGGER.debug("CampingCareHA: response data: %s", data)
#                     if connection:
#                         connection.send_message({
#                             "id": msg["id"],
#                             "type": "result",
#                             "success": True,
#                             "result": data
#                         })
#                 else:
#                     if connection:
#                         connection.send_error(msg["id"], "api_error", f"API error: {response.status}")
#     except ClientError as e:
#         _LOGGER.error("API request failed: %s", e)
#         if connection:
#             connection.send_error(msg["id"], "api_exception", str(e))
