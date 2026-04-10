"""API client for the Molekule Air integration."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import socket
import time
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

# Refresh the access token when it expires within this many seconds.
_TOKEN_REFRESH_BUFFER = 300  # 5 minutes


class MolekuleApiError(Exception):
    """Base exception for Molekule API errors."""


class MolekuleAuthenticationError(MolekuleApiError):
    """Raised when authentication with Molekule fails."""


def _parse_token_expiry(access_token: str) -> float:
    """Return the ``exp`` claim from a JWT access token, or 0 on failure."""
    try:
        payload_b64 = access_token.split(".")[1]
        # JWT uses base64url without padding — add it back.
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return float(payload.get("exp", 0))
    except Exception:  # noqa: BLE001
        return 0


def _login(username: str, password: str) -> Cognito:
    """Create a new authenticated Cognito session (blocking)."""
    cog = Cognito(
        COGNITO_USER_POOL_ID,
        COGNITO_APP_CLIENT_ID,
        username=username,
    )
    cog.authenticate(password=password)
    return cog


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
        self._auth: Cognito | None = None
        self._token_expires_at: float = 0
        self._auth_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch all devices for the configured Molekule account."""
        return await self._api_request("get", "devices")

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
            await self._api_request(
                "post",
                f"devices/{device_serial}/actions/set-power-status",
                {"status": "off"},
            )
            return

        if power == "on":
            await self._api_request(
                "post",
                f"devices/{device_serial}/actions/set-power-status",
                {"status": "on"},
            )

        if mode in {MODE_SMART, MODE_MANUAL}:
            await self._api_request(
                "post",
                f"devices/{device_serial}/actions/{mode}",
            )

        if speed is not None:
            await self._api_request(
                "post",
                f"devices/{device_serial}/actions/set-fan-speed",
                {"fanSpeed": int(speed)},
            )

    async def async_verify_auth(self) -> bool:
        """Return whether the configured credentials are valid."""
        try:
            auth = await self._async_ensure_auth(force_login=True)
            await self._hass.async_add_executor_job(auth.verify_tokens)
        except (MolekuleAuthenticationError, Exception):  # noqa: BLE001
            return False
        return True

    # ------------------------------------------------------------------
    # Auth management
    # ------------------------------------------------------------------

    async def _async_ensure_auth(
        self, *, force_login: bool = False
    ) -> Cognito:
        """Return a valid Cognito session, refreshing only when needed."""
        async with self._auth_lock:
            if force_login or self._auth is None:
                return await self._do_login()

            # Only refresh if the token is close to expiring.
            if time.time() >= self._token_expires_at - _TOKEN_REFRESH_BUFFER:
                _LOGGER.debug("Access token near expiry, refreshing")
                try:
                    await self._hass.async_add_executor_job(
                        self._auth.check_token
                    )
                    self._token_expires_at = _parse_token_expiry(
                        self._auth.access_token
                    )
                except Exception:  # noqa: BLE001
                    _LOGGER.debug(
                        "Token refresh failed, performing full login"
                    )
                    return await self._do_login()

            return self._auth

    async def _do_login(self) -> Cognito:
        """Perform a fresh Cognito login and cache the result."""
        try:
            auth = await self._hass.async_add_executor_job(
                _login, self._username, self._password
            )
        except Exception as err:  # noqa: BLE001
            raise MolekuleAuthenticationError(
                "Unable to authenticate with Molekule"
            ) from err

        self._auth = auth
        self._token_expires_at = _parse_token_expiry(auth.access_token)
        _LOGGER.debug(
            "Logged in to Molekule, token expires at %s",
            self._token_expires_at,
        )
        return auth

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    async def _api_request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        *,
        _retried: bool = False,
    ) -> dict[str, Any]:
        """Execute a Molekule API request with automatic auth retry."""
        auth = await self._async_ensure_auth()
        url = f"{MOLEKULE_API_BASE_URL}/{path.lstrip('/')}"
        headers = {
            "accept": "application/json",
            "authorization": auth.access_token,
            "content-type": "application/json",
            "user-agent": _USER_AGENT,
            "x-api-version": "1.0",
        }

        try:
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.request(
                    method.upper(),
                    url,
                    headers=headers,
                    json=json_body,
                ) as response:
                    if response.status in {401, 403} and not _retried:
                        _LOGGER.debug(
                            "API returned %s for %s, re-authenticating",
                            response.status,
                            path,
                        )
                        async with self._auth_lock:
                            await self._do_login()
                        return await self._api_request(
                            method, path, json_body, _retried=True
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
