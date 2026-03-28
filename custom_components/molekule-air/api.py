"""API client for the Molekule Air integration."""
from __future__ import annotations

import asyncio
import logging
import socket
from typing import Any

import aiohttp
import async_timeout
from pycognito import Cognito

from homeassistant.core import HomeAssistant

from .const import (
    COGNITO_APP_CLIENT_ID,
    COGNITO_USER_POOL_ID,
    MODE_MANUAL,
    MODE_SMART,
    MOLEKULE_API_BASE_URL,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__package__)

_USER_AGENT = (
    "Molekule/3.1.3 (com.molekule.ios; build:1167; iOS 14.0.0) "
    "Alamofire/4.9.1"
)


class MolekuleApiError(Exception):
    """Base exception for Molekule API errors."""


class MolekuleAuthenticationError(MolekuleApiError):
    """Raised when authentication with Molekule fails."""


def login(username: str, password: str) -> Cognito:
    """Create a new authenticated Cognito session."""
    response = Cognito(
        COGNITO_USER_POOL_ID,
        COGNITO_APP_CLIENT_ID,
        username=username,
    )
    response.authenticate(password=password)
    return response


async def async_login(
    hass: HomeAssistant,
    username: str,
    password: str,
) -> Cognito:
    """Run the Cognito login flow in the executor."""
    return await hass.async_add_executor_job(login, username, password)


async def async_refresh_auth(hass: HomeAssistant, response: Cognito) -> Cognito:
    """Refresh the current Cognito token set if needed."""

    def _refresh() -> Cognito:
        response.check_token()
        return response

    return await hass.async_add_executor_job(_refresh)


class MolekuleApiClient:
    """Thin client for the Molekule cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._hass = hass
        self._username = username
        self._password = password
        self._session = session
        self.auth_response: Cognito | None = None

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch all devices for the configured Molekule account."""
        return await self.api_wrapper("get", "devices")

    async def async_set_data(
        self,
        device_serial: str,
        data: dict[str, Any],
    ) -> None:
        """Apply a state change to a Molekule device."""
        speed = data.get("speed")
        power = data.get("power")
        mode = data.get("mode")

        _LOGGER.debug("Applying state change for %s: %s", device_serial, data)

        if power == "off":
            await self.api_wrapper(
                "post",
                f"devices/{device_serial}/actions/set-power-status",
                {"status": "off"},
            )
            return

        if power == "on":
            await self.api_wrapper(
                "post",
                f"devices/{device_serial}/actions/set-power-status",
                {"status": "on"},
            )

        if mode in {MODE_SMART, MODE_MANUAL}:
            await self.api_wrapper(
                "post",
                f"devices/{device_serial}/actions/{mode}",
            )

        if speed is not None:
            await self.api_wrapper(
                "post",
                f"devices/{device_serial}/actions/set-fan-speed",
                {"fanSpeed": int(speed)},
            )

    async def async_verify_auth(self) -> bool:
        """Return whether the configured credentials are valid."""
        try:
            auth_response = await self._async_get_auth_response(force_login=True)
            await self._hass.async_add_executor_job(auth_response.verify_tokens)
        except MolekuleAuthenticationError:
            return False
        return True

    async def api_wrapper(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        *,
        retry_on_auth: bool = True,
    ) -> dict[str, Any]:
        """Execute a Molekule API request."""
        auth_response = await self._async_get_auth_response()
        url = f"{MOLEKULE_API_BASE_URL}/{path.lstrip('/')}"
        headers = self._build_headers(auth_response.access_token)

        try:
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.request(
                    method.upper(),
                    url,
                    headers=headers,
                    json=json_body,
                ) as response:
                    if response.status in {401, 403} and retry_on_auth:
                        _LOGGER.debug(
                            "Molekule API rejected cached auth for %s, retrying login",
                            path,
                        )
                        self.auth_response = None
                        await self._async_get_auth_response(force_login=True)
                        return await self.api_wrapper(
                            method,
                            path,
                            json_body,
                            retry_on_auth=False,
                        )

                    response.raise_for_status()
                    return await self._parse_response(response, url)
        except asyncio.TimeoutError as err:
            raise MolekuleApiError(f"Timeout talking to {url}") from err
        except aiohttp.ClientResponseError as err:
            if err.status in {401, 403}:
                raise MolekuleAuthenticationError(
                    "Molekule rejected the current credentials"
                ) from err
            raise MolekuleApiError(
                f"Molekule API returned HTTP {err.status} for {url}"
            ) from err
        except (aiohttp.ClientError, socket.gaierror) as err:
            raise MolekuleApiError(f"Error talking to {url}") from err

    async def _async_get_auth_response(self, *, force_login: bool = False) -> Cognito:
        """Return a valid Cognito session, refreshing or re-authenticating as needed."""
        if force_login or self.auth_response is None:
            self.auth_response = await self._async_login()
            return self.auth_response

        try:
            self.auth_response = await async_refresh_auth(self._hass, self.auth_response)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug(
                "Refreshing Molekule auth failed, falling back to login: %s",
                err,
            )
            self.auth_response = await self._async_login()

        return self.auth_response

    async def _async_login(self) -> Cognito:
        """Perform a fresh Cognito login."""
        try:
            return await async_login(self._hass, self._username, self._password)
        except Exception as err:  # pylint: disable=broad-except
            raise MolekuleAuthenticationError(
                "Unable to authenticate with Molekule"
            ) from err

    async def _parse_response(
        self,
        response: aiohttp.ClientResponse,
        url: str,
    ) -> dict[str, Any]:
        """Return a JSON response body when present."""
        if response.status == 204 or response.content_length == 0:
            return {}

        content_type = response.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            raw_response = await response.text()
            if raw_response:
                _LOGGER.debug("Non-JSON response from %s: %s", url, raw_response)
            return {}

        try:
            return await response.json()
        except (aiohttp.ContentTypeError, ValueError) as err:
            raise MolekuleApiError(f"Invalid JSON response from {url}") from err

    def _build_headers(self, access_token: str) -> dict[str, str]:
        """Build a request header set for Molekule API calls."""
        return {
            "accept": "application/json",
            "authorization": access_token,
            "content-type": "application/json",
            "user-agent": _USER_AGENT,
            "x-api-version": "1.0",
        }
