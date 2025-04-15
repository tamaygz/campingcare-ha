import logging
import voluptuous as vol

from homeassistant import config_entries  # Ensure Home Assistant is installed in your environment
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.components import websocket_api

from .const import DOMAIN, CONF_API_KEY, CONF_API_URL, CONF_NAME

from aiohttp import ClientError, ClientConnectionError, ClientSession, InvalidURL, web, web_response
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
    """Set up CampingCareHA integration from YAML (unused)."""
    _LOGGER.info("CampingCareHA: async_setup called — skipping YAML config.")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up CampingCareHA from a config entry."""
    _LOGGER.info("Setting up CampingCareHA for %s", entry.data[CONF_NAME])

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
        "campingcareha/query_license_plate"
    )

    return True

async def test_api_connection(url: str, api_key: str):
    """Test the API connection."""
    try:
        async with ClientSession() as session:
            async with session.get(f"{url}/v1/test", headers={"Authorization": f"Bearer {api_key}"}) as response:
                if response.status == 200:
                    _LOGGER.info("Successfully connected to CampingCare API")
                    return True
                _LOGGER.warning("CampingCare API returned status %s", response.status)
    except ClientError as e:
        _LOGGER.error("Error connecting to CampingCare API: %s", e)
    return False

async def websocket_query_license_plate(hass: HomeAssistant, connection, msg):
    """Handle WebSocket license plate lookup."""
    plate = msg.get("plate")
    entry_id = msg.get("entry_id")

    if not plate or not entry_id or entry_id not in hass.data[DOMAIN]:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Missing or invalid plate/entry_id")
        return

    api_info = hass.data[DOMAIN][entry_id]
    url = api_info[CONF_API_URL]
    api_key = api_info[CONF_API_KEY]

    try:
        async with ClientSession() as session:
            async with session.get(
                f"{url}/v1/guests?plate={plate}",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    connection.send_message({
                        "id": msg["id"],
                        "type": "result",
                        "success": True,
                        "result": data
                    })
                else:
                    connection.send_error(msg["id"], "api_error", f"API error: {response.status}")
    except ClientError as e:
        _LOGGER.error("API request failed: %s", e)
        connection.send_error(msg["id"], "api_exception", str(e))
