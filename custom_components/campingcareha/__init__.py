import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import websocket_api
from homeassistant.helpers.event import async_call_later  # Import async_call_later directly

from .const import DOMAIN, CONF_API_KEY, CONF_API_URL, CONF_NAME

from aiohttp import ClientError, ClientConnectionError, ClientSession, InvalidURL, web, web_response
from aiohttp.web_exceptions import HTTPBadRequest

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the CampingCare integration."""
    _LOGGER.info("CampingCareHA: async_setup called — skipping YAML config.")

    async def handle_query_plate(call: ServiceCall):
        """Handle the query_plate service."""
        plate = call.data.get("plate")
        entry_id = list(hass.data[DOMAIN].keys())[0] if hass.data[DOMAIN] else None

        if not entry_id:
            _LOGGER.error("No valid CampingCareHA entry found.")
            return

        # Create a mock WebSocket message
        msg = {
            "id": "service_call",  # Use a placeholder ID
            "plate": plate,
            "entry_id": entry_id,
        }

        # Call the existing WebSocket method
        _LOGGER.debug("Calling websocket_query_license_plate with plate: %s", plate)
        await websocket_query_license_plate(hass, None, msg)

    # Register the service
    hass.services.async_register(
        domain="campingcareha",
        service="query_plate",
        service_func=handle_query_plate,
        schema=vol.Schema({
            vol.Required("plate"): str,
        }),
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up CampingCareHA from a config entry."""
    _LOGGER.info("Setting up CampingCareHA for %s", entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NAME: entry.data[CONF_NAME],
        CONF_API_KEY: entry.data[CONF_API_KEY],
        CONF_API_URL: entry.data[CONF_API_URL],
    }

    # Validate API connection
    if not await test_api_connection(entry.data[CONF_API_URL], entry.data[CONF_API_KEY]):
        _LOGGER.error("CampingCareHA API connection failed.")
        return False

    websocket_api.async_register_command(
        hass,
        websocket_query_license_plate,
        f"{DOMAIN}/query_license_plate"
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.info("Unloaded CampingCareHA entry '%s'", entry.entry_id)
    return True

async def test_api_connection(url: str, api_key: str):
    """Test the API connection."""
    try:
        async with ClientSession() as session:
            async with session.get(f"{url}/version", headers={"Authorization": f"Bearer {api_key}"}) as response:
                if response.status == 200:
                    _LOGGER.debug("CampingCareHA: API test successful.")
                    return True
                _LOGGER.warning("CampingCareHA: API test returned status %s", response.status)
    except ClientError as e:
        _LOGGER.error("CampingCareHA: API test failed: %s", e)
    return False

async def websocket_query_license_plate(hass: HomeAssistant, connection, msg):
    """Handle WebSocket license plate lookup."""
    plate = msg.get("plate")
    entry_id = msg.get("entry_id")
    
    # Log the entry_id for debugging
    _LOGGER.debug("WebSocket query_license_plate called with plate: %s", plate)

    if not plate or not entry_id or entry_id not in hass.data[DOMAIN]:
        if connection:
            connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Missing or invalid plate/entry_id")
        return

    config = hass.data[DOMAIN][entry_id]
    url = config[CONF_API_URL]
    api_key = config[CONF_API_KEY]

    try:
        async with ClientSession() as session:
            async with session.get(
                f"{url}/license_plates/check_plate?plate={plate}",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if connection:
                        connection.send_message({
                            "id": msg["id"],
                            "type": "result",
                            "success": True,
                            "result": data
                        })
                else:
                    if connection:
                        connection.send_error(msg["id"], "api_error", f"API error: {response.status}")
    except ClientError as e:
        _LOGGER.error("API request failed: %s", e)
        if connection:
            connection.send_error(msg["id"], "api_exception", str(e))
