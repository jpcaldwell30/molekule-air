"""Sample API Client."""
from datetime import date, datetime, timedelta
import json
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
    MOLEKCULE_SUGGESTED_HOST,
    TIMEOUT,
)

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)


def login(username: str, password: str) -> Cognito:
    """Generate fresh credentials"""
    resp = Cognito(COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID, username=username)
    resp.authenticate(password=password)
    return resp

@staticmethod
async def async_login(hass: HomeAssistant, username: str, password: str) -> Cognito:
    """Log in."""

    def _login(username: str, password: str) -> Cognito:
        """Log in."""
        try:
            response = login(username, password)  # login returns Cognito
        except Exception as err:  # pylint: disable=broad-except
            raise err
        expires_at = (datetime.now() + timedelta(seconds=3600)).timestamp()
        _LOGGER.debug("Login successful, token expires %d", expires_at)
        return response  # needs to return Cognito

    return await hass.async_add_executor_job(_login, username, password)


@staticmethod
async def async_refresh_auth(hass: HomeAssistant, response: Cognito) -> Cognito:
    def _refresh(response: Cognito) -> Cognito:
        try:
            response.check_token()
        except Exception as err:  # pylint: disable=broad-except
            raise err
        return response

    return await hass.async_add_executor_job(_refresh, response)


class MolekuleApiClient:
    auth_response: Cognito

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._username = username
        self._password = password
        self._session = session
        self._hass = hass

    async def async_get_data(self) -> dict:
        """This will get data from https://api.molekule.com/users/me/devices"""
        return await self.api_wrapper(method="get", path="devices")

    async def async_set_data(self, device_serial, data: dict[str, Any]) -> None: # data: dict[str, Any]
        speed = data.get("speed", None)
        power = data.get("power", None)
        mode = data.get("mode", None)
        _LOGGER.debug("attempting to set state of device. Data is %s", data)
        if power:
            url = 'devices/' + device_serial + '/actions' + '/set-power-status'
            dataBody = {
                "status": power
            }
            _LOGGER.debug("path: %s, dataBody: %s", url, dataBody )
            await self.api_wrapper(method="post", path=url, kwargs=dataBody)
        if speed:
            url = 'devices/' + device_serial + '/actions' + '/set-fan-speed'
            dataBody = {
                "fanSpeed": speed
            }
            _LOGGER.debug("path: %s, dataBody: %s", url, dataBody )
            await self.api_wrapper(method="post", path=url, kwargs=dataBody)
        # if mode:
        #     url = 'devices/' + device_serial + '/actions' + '/set-fan-speed'
        #     dataBody = {
        #         "fanSpeed": speed
        #     }
        #     _LOGGER.debug("path: %s, dataBody: %s", url, dataBody )
        #     await self.api_wrapper(method="post", path=url, kwargs=dataBody)

    async def async_verify_auth(self) -> bool:
        self.auth_response = await async_login(
            hass=self._hass, username=self._username, password=self._password
        )
        # _LOGGER.debug(
        #     "Attempting to verify with id token %s and acess token %s",
        #     self.auth_response.id_token,
        #     self.auth_response.access_token,
        # )
        try:
            self.auth_response.verify_tokens()
            self.auth_response.check_token()
            return True
        except:
            return False

    async def api_wrapper(self, method: str, path: str, **kwargs) -> dict:
        """Get information from the API."""
        data = kwargs.get("data")
        headers = kwargs.get("headers")
        args = kwargs.get("kwargs")
        # _LOGGER.debug("data is %s", data)
        # _LOGGER.debug("args are %s", args)
        # Make a request
        # _LOGGER.debug("access token is %s", self._auth_response.access_token)
        if self.auth_response.access_token:
            self.auth_response = await async_refresh_auth(
                self._hass, self.auth_response
            )
        else:
            self.auth_response = await async_login(
                self._hass, self._username, self._password
            )
        if data is None:
            data = {}
        else:
            data = dict(data)

        if headers is None:
            headers = {}
        else:
            headers = dict(headers)

        #_LOGGER.debug("data is %s", data)
        #_LOGGER.debug("args are %s", args)
        #_LOGGER.debug("Headers data is %s", headers)

        headers["authorization"] = self.auth_response.access_token
        headers["x-api-version"] = "1.0"
        headers["host"] = "api.molekule.com"
        headers["accept"] = "application/json"
        headers["content-type"] = "application/json"
        headers[
            "user-agent"
        ] = "Molekule/3.1.3 (com.molekule.ios; build:1167; iOS 14.0.0) Alamofire/4.9.1"
        headers["Date"] = date.today().strftime("%a, %d %b %Y %H:%M:%S GMT")

        url = f"{MOLEKCULE_SUGGESTED_HOST}/{path}"  # check
        try:
            async with async_timeout.timeout(TIMEOUT):
                #_LOGGER.debug("method: %s", method)
                if method == "get":
                    #_LOGGER.debug("Trying to get data from API")
                    response = await self._session.get(url, headers=headers)
                    jsonResponse = await response.json()
                    json_string = json.dumps(jsonResponse, indent=4)
                    #_LOGGER.debug("Response data is %s", json_string)
                    # return json_string
                    return json.loads(json_string)
                if method == "put":
                    response = await self._session.put(url, headers=headers, json=args)
                    jsonResponse = await response.json()
                    json_string = json.dumps(jsonResponse, indent=4)
                    _LOGGER.debug("Response data is %s", json_string)
                    # return json_string
                    # return json.loads(json_string)

                if method == "patch":
                    await self._session.patch(url, headers=headers, json=data)

                if method == "post":
                    response = await self._session.post(url, headers=headers, json=args)
                    _LOGGER.debug("Response data is %s", response)
                    # jsonResponse = await response.json()
                    # json_string = json.dumps(jsonResponse, indent=4)
                    # _LOGGER.debug("Response data is %s", json_string)
                    # return json_string
                    # return json.loads(json_string)

        except TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
