from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_API_KEY, CONF_API_URL, CONF_NAME


class CampingCareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CampingCare."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_NAME]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_API_URL): str,
            vol.Required(CONF_API_KEY): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
