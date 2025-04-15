import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api

from .const import DOMAIN, CONF_NAME, CONF_API_KEY, CONF_API_URL
from .options_flow import CampingCareOptionsFlowHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up CampingCareHA integration (YAML not supported)."""
    _LOGGER.debug("CampingCareHA: async_setup called — no YAML support.")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up CampingCareHA from a config entry."""
    _LOGGER.info("Setting up CampingCareHA for '%s'", entry.data[CONF_NAME])

    hass.data.setdefault(DOMAIN, {})

    # Use updated values from options if available
    api_key = entry.options.get(CONF_API_KEY, entry.data[CONF_API_KEY])
    api_url = entry.options.get(CONF_API_URL, entry.data[CONF_API_URL])
    name = entry.options.get(CONF_NAME, entry.data[CONF_NAME])

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NAME: name,
        CONF_API_KEY: api_key,
        CONF_API_URL: api_url,
    }

    if not await test_api_connection(api_url, api_key):
        _LOGGER.error("CampingCareHA: API test failed for '%s'", name)
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
    _LOGGER.info("CampingCareHA: Unloaded entry '%s'", entry.entry_id)
    return True


async def async_get_options_flow(config_entry: ConfigEntry):
    """Return the options flow handler."""
    return CampingCareOptionsFlowHandler(config_entry)


async def test_api_connection(url: str, api_key: str) -> bool:
    """Test the API connection."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/v1/test", headers={"Authorization": f"Bearer {api_key}"}) as response:
                if response.status == 200:
                    _LOGGER.debug("CampingCareHA: API test successful")
                    return True
                _LOGGER.warning("CampingCareHA: API test returned status %s", response.status)
    except aiohttp.ClientError as e:
        _LOGGER.error("CampingCareHA: API test exception: %s", e)
    return False


async def websocket_query_license_plate(hass: HomeAssistant, connection, msg):
    """Handle WebSocket request to look up a guest by license plate."""
    plate = msg.get("plate")
    entry_id = msg.get("entry_id")

    if not plate or not entry_id or entry_id not in hass.data[DOMAIN]:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Missing or invalid plate/entry_id")
        return

    config = hass.data[DOMAIN][entry_id]
    url = config[CONF_API_URL]
    api_key = config[CONF_API_KEY]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{url}/v1/guests?plate={plate}",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                if response.status == 200:
                    guest_data = await response.json()
                    connection.send_result(msg["id"], guest_data)
                else:
                    connection.send_error(msg["id"], "api_error", f"API error: {response.status}")
    except aiohttp.ClientError as e:
        _LOGGER.error("CampingCareHA: Guest lookup failed: %s", e)
        connection.send_error(msg["id"], "api_exception", str(e))
