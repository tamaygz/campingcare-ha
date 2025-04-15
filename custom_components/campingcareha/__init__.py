import logging
import voluptuous as vol

from homeassistant import config_entries  # Ensure Home Assistant is installed in your environment
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.components import websocket_api

from .const import DOMAIN, CONF_API_KEY, CONF_API_URL, CONF_NAME

from aiohttp import ClientConnectionError, ClientSession, InvalidURL, web, web_response
from aiohttp.web_exceptions import HTTPBadRequest

_LOGGER = logging.getLogger(__name__)

# Define configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_API_URL): cv.url,
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the CampingCare integration."""
    _LOGGER.info("Setting up CampingCare integration")

    if DOMAIN not in config:
        return True

    return await async_setup_entry(hass, config[DOMAIN])

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up CampingCare from a config entry."""
    _LOGGER.info("Setting up CampingCare for %s", entry.data[CONF_NAME])

    name = entry.data[CONF_NAME]
    api_key = entry.data[CONF_API_KEY]
    url = entry.data[CONF_API_URL]

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NAME: name,
        CONF_API_KEY: api_key,
        CONF_API_URL: url,
    }

    # Make an initial API call to verify credentials
    if not await test_api_connection(url, api_key):
        _LOGGER.error("API connection failed for %s", entry.data[CONF_NAME])
        return False

    # Add a websocket command for querying the license plate
    websocket_api.async_register_command(
        hass, websocket_query_license_plate, "campingcare/query_license_plate"
    )

    return True

async def test_api_connection(url: str, api_key: str):
    """Test the API connection to ensure it's working."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/v1/test", headers={"Authorization": f"Bearer {api_key}"}) as response:
                if response.status == 200:
                    _LOGGER.info("Successfully connected to the CampingCare API")
                    return True
                else:
                    _LOGGER.error("Failed to connect to the API. Status code: %s", response.status)
                    return False
    except aiohttp.ClientError as e:
        _LOGGER.error("Error connecting to the API: %s", str(e))
        return False

async def websocket_query_license_plate(hass: HomeAssistant, connection, msg):
    """Handle the websocket command for querying license plate data."""
    plate = msg.get("plate")

    # Ensure that the license plate is provided
    if not plate:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Missing license plate")
        return

    # Retrieve the stored API data
    url = hass.data[DOMAIN][msg["entry_id"]][CONF_API_URL]
    api_key = hass.data[DOMAIN][msg["entry_id"]][CONF_API_KEY]

    # Make the API call to fetch guest data by license plate
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/v1/guests?plate={plate}", headers={"Authorization": f"Bearer {api_key}"}) as response:
                if response.status == 200:
                    data = await response.json()
                    connection.send_message({
                        "id": msg["id"],
                        "type": "result",
                        "data": data
                    })
                else:
                    connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Failed to retrieve data")
    except aiohttp.ClientError as e:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, f"Error: {str(e)}")
