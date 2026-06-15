"""Config flow for the DR LYD integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DRLydAuthError, DRLydClient, DRLydError
from .const import CONF_API_KEY, DEFAULT_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DRLydConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DR LYD."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            session = async_get_clientsession(self.hass)
            client = DRLydClient(session, api_key)
            try:
                await client.async_validate()
            except DRLydAuthError:
                errors["base"] = "invalid_auth"
            except DRLydError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="DR LYD",
                    data={CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY, default=DEFAULT_API_KEY
                    ): str,
                }
            ),
            errors=errors,
        )
