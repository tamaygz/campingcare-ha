import logging
import aiohttp

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_API_KEY, CONF_API_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the CampingCare integration (needed for config flow)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up one CampingCare instance from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NAME: entry.data[CONF_NAME],
        CONF_API_KEY: entry.data[CONF_API_KEY],
        CONF_API_URL: entry.data[CONF_API_URL],
    }

    async def handle_query_plate(call: ServiceCall):
        """Handle the query_plate service call."""
        plate = call.data.get("plate")
        if not plate:
            _LOGGER.error("No license plate provided.")
            return

        api_key = entry.data[CONF_API_KEY]
        api_url = entry.data.get(CONF_API_URL)

        url = f"{api_url}/guests?plate={plate}"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        guest_data = await response.json()
                        _LOGGER.info(f"Guest found for plate {plate}: {guest_data}")
                    elif response.status == 404:
                        _LOGGER.warning(f"No guest found for plate {plate}")
                    else:
                        text = await response.text()
                        _LOGGER.error(f"API error {response.status}: {text}")
            except aiohttp.ClientError as e:
                _LOGGER.error(f"API request failed: {e}")

    hass.services.async_register(DOMAIN, "query_plate", handle_query_plate)

    return True
