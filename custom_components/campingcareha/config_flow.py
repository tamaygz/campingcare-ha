"""Config flow for CampingCare HA integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
# from homeassistant.data_entry_flow import FlowResult
from .const import (DOMAIN, CONF_NAME, CONF_API_KEY, CONF_API_URL, DEFAULT_API_URL)

# _LOGGER = logging.getLogger(__name__)

class CampingCareConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CampingCare HA."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step of the config flow."""       
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )


        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
            vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return CampingCareOptionsFlowHandler()   

    
class CampingCareOptionsFlowHandler(OptionsFlow):
    """Handle CampingCareHA options."""

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the CampingCareHA options."""
        if user_input is not None:
            # Save new options
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                options=user_input,
                title=user_input[CONF_NAME],
            )

            # Trigger reload so UI reflects new title
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(data=user_input)

        # Prefer options if present, otherwise use the original config entry data
        name = self.config_entry.options.get(CONF_NAME, self.config_entry.data.get(CONF_NAME))
        api_url = self.config_entry.options.get(CONF_API_URL, self.config_entry.data.get(CONF_API_URL))
        api_key = self.config_entry.options.get(CONF_API_KEY, self.config_entry.data.get(CONF_API_KEY))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=name): str,
                vol.Required(CONF_API_URL, default=api_url): str,
                vol.Required(CONF_API_KEY, default=api_key): str,
            }),
            errors={"base": translations["errors.api_connection_failed"]},
        )
