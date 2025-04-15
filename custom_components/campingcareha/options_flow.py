# options_flow.py

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import (DOMAIN, CONF_API_KEY, CONF_API_URL, CONF_NAME, DEFAULT_API_URL)

@config_entries.HANDLERS.register(DOMAIN)
class CampingCareOptionsFlowHandler(config_entries.OptionsFlow, domain=DOMAIN):
    """Handle CampingCareHA options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the CampingCareHA options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=self.config_entry.data.get(CONF_NAME)): str,
                vol.Required(CONF_API_URL, default=self.config_entry.data.get(CONF_API_URL, DEFAULT_API_URL)): str,
                vol.Required(CONF_API_KEY, default=self.config_entry.data.get(CONF_API_KEY)): str,
            })
        )
