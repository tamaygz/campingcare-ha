import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY, CONF_URL
import voluptuous as vol
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CampingCareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CampingCare."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step of the config flow."""
        if user_input is not None:
            # Here you can validate the API key and URL
            api_key = user_input[CONF_API_KEY]
            url = user_input[CONF_URL]

            # If validation succeeds, create a config entry
            return self.async_create_entry(
                title="CampingCare Integration",
                data={
                    CONF_API_KEY: api_key,
                    CONF_URL: url
                }
            )

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_data_schema()
        )

    def _get_data_schema(self):
        """Return the schema for the data input fields."""
        from homeassistant.helpers import config_validation as cv

        return vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_URL): str,
        })
