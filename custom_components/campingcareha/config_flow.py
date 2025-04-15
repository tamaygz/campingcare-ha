import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_NAME, CONF_API_KEY, CONF_API_URL


_LOGGER = logging.getLogger(__name__)

class CampingCareConfigFlow(config_entries.ConfigEntry, domain=DOMAIN):
    """Handle a config flow for CampingCare."""

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step of the config flow."""
        errors = {}


        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_NAME]}")
            self._abort_if_unique_id_configured()

            # If validation succeeds, create a config entry
            return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
            )

        # Define the schema for user input
        data_schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_API_URL): str,
            vol.Required(CONF_API_KEY): str,
        })

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )