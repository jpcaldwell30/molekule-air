"""Config flow for Molekule purifier."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol
from . import auth

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant import data_entry_flow

from .const import MOLEKULE_AUTH_RESPONSE, MOLEKULE_DOMAIN, MOLEKULE_NAME
from .helpers import Helpers, MolekuleException

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("hello from molekule config flow")
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})

AUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

@config_entries.HANDLERS.register(MOLEKULE_DOMAIN)
class MolekuleFlowHandler(config_entries.ConfigFlow, domain=MOLEKULE_DOMAIN):
    """Config flow handler."""

    VERSION = 1

    def __init__(self) -> None:
        """Start a config flow."""
        self._reauth_unique_id = None
        _LOGGER.debug("MolekuleFlowHandler init")

    async def _validate_input(self, username: str, password: str):
        """Validate the user input."""
        try:
            auth_response = await Helpers.async_login(self.hass, username, password)
            return {"errors": None, MOLEKULE_AUTH_RESPONSE: auth_response}
        except MolekuleException as err:
            if err.result_code == "UserNotFoundException":
                return {"errors": {"base": "invalid_user"}, MOLEKULE_AUTH_RESPONSE: None}

            return {
                "errors": {"base": "invalid_auth"},
                MOLEKULE_AUTH_RESPONSE: None,
            }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""

        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            errors_and_auth = await self._validate_input(
                username, user_input[CONF_PASSWORD]
            )
            errors = errors_and_auth["errors"]
            if not errors:
                auth_response: auth.MolekuleAuthResponse = errors_and_auth[
                    MOLEKULE_AUTH_RESPONSE
                ]
                await self.async_set_unique_id(username)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=MOLEKULE_NAME,
                    data={**user_input, MOLEKULE_AUTH_RESPONSE: auth_response},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_DATA_SCHEMA,
            errors=errors,
        )
    
    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        # pylint: disable=unused-argument
        """Handle reauthentication."""
        self._reauth_unique_id = self.context["unique_id"]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauthentication."""
        errors = {}
        existing_entry = await self.async_set_unique_id(self._reauth_unique_id)
        username = existing_entry.data[CONF_USERNAME]
        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            errors_and_auth = await self._validate_input(username, password)
            errors = errors_and_auth["errors"]
            if not errors:
                auth_response = errors_and_auth[MOLEKULE_AUTH_RESPONSE]
                self.hass.config_entries.async_update_entry(
                    existing_entry,
                    data={
                        **existing_entry.data,
                        CONF_PASSWORD: password,
                        MOLEKULE_AUTH_RESPONSE: auth_response,
                    },
                )
                await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            description_placeholders={CONF_USERNAME: username},
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
        )

# AUTH_DATA_SCHEMA = vol.Schema(
#     {
#         vol.Required(CONF_USERNAME): str,
#         vol.Required(CONF_PASSWORD): str,
#     }
# )
# @config_entries.HANDLERS.register(MOLEKULE_DOMAIN)
# class MolekuleFlowHandler(config_entries.ConfigFlow, domain=MOLEKULE_DOMAIN):
#     """Config flow handler."""

#     VERSION = 1
#     def __init__(self) -> None: 
#         """Start a config flow."""
#         self._reauth_unique_id = None
#         _LOGGER.debug("MolekuleFlowHandler init")

#     async def _validate_input(self, username: str, password: str):
#         """Validate the user input."""
#         try:
#             auth_response = await Helpers.async_login(self.hass, username, password)
#             return {"errors": None, MOLEKULE_AUTH_RESPONSE: auth_response}
#         except MolekuleException as err:
#             if err.result_code == "UserNotFoundException":
#                 return {"errors": {"base": "invalid_user"}, MOLEKULE_AUTH_RESPONSE: None}

#             return {
#                 "errors": {"base": "invalid_auth"},
#                 MOLEKULE_AUTH_RESPONSE: None,
#             }

#     async def async_step_user(
#         self, user_input: dict[str, Any] | None = None
#     ) -> FlowResult:
#         """Handle a flow initialized by the user."""

#         errors: dict[str, str] = {}
#         if user_input is not None:
#             username = user_input[CONF_USERNAME]
#             errors_and_auth = await self._validate_input(
#                 username, user_input[CONF_PASSWORD]
#             )
#             errors = errors_and_auth["errors"]
#             if not errors:
#                 auth_response: auth.MolekuleAuthResponse = errors_and_auth[
#                     MOLEKULE_AUTH_RESPONSE
#                 ]
#                 await self.async_set_unique_id(username)
#                 self._abort_if_unique_id_configured()
#                 return self.async_create_entry(
#                     title=MOLEKULE_NAME,
#                     data={**user_input, MOLEKULE_AUTH_RESPONSE: auth_response},
#                 )

#         return self.async_show_form(
#             step_id="user",
#             data_schema=AUTH_DATA_SCHEMA,
#             errors=errors,
#         )