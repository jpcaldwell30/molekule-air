"""Config flow for Molekule Air integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import MolekuleApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="password")
        ),
    }
)


class MolekuleFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Molekule Air."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize the flow handler."""
        self._errors: dict[str, str] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

            self._errors["base"] = "invalid_auth"

        return self._show_config_form()

    def _show_config_form(self) -> config_entries.ConfigFlowResult:
        """Show the configuration form."""
        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_DATA_SCHEMA,
            errors=self._errors,
        )

    async def _test_credentials(self, username: str, password: str) -> bool:
        """Return whether the supplied credentials are valid."""
        _LOGGER.debug("Validating Molekule login for %s", username)
        client = MolekuleApiClient(
            self.hass,
            username,
            password,
            async_get_clientsession(self.hass),
        )
        return await client.async_verify_auth()
