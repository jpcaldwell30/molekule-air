"""The MolekuleDriver component."""

from __future__ import annotations

import logging

import aiohttp
import json

_LOGGER = logging.getLogger(__name__)

class MolekuleDriver:
    """MolekuleDevice driver."""

    # pylint: disable=line-too-long
    CTRL_URL = "https://api.molekule.com/users/me/devices/{serial}/actions/{action}"
    STATE_URL = "https://api.molekule.com/users/me/devices"
    #STATE_URL = "https://api.molekule.com/users/me/devices/{serial}"
    # PARAM_URL = "https://us.api.winix-iot.com/common/event/param/devices/{deviceid}"
    # CONNECTED_STATUS_URL = (
    #     "https://us.api.winix-iot.com/common/event/connsttus/devices/{deviceid}"
    # )

    state_keys = {
        "power": {"off": "0", "on": "1"},
        "power_command": {"off":{"status": "off"}, "on": {"status": "on"}},
        "mode": {"smart": "smart", "manual": "manual", "off": "off"},
        "airflow": {
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
        },
        "fan_speed": {
            "1": {"fanSpeed": 1}, 
            "2": {"fanSpeed": 2},
            "3": {"fanSpeed": 3},
            "4": {"fanSpeed": 4},
            "5": {"fanSpeed": 5},
            "6": {"fanSpeed": 6},
        },
        "silent": {"off": "0", "on": "1"},
        #"plasma": {"off": "0", "on": "1"},
        "air_quality": {"good": "good", "fair": "far", "moderate": "moderate", "poor": "poor"},
        "action": {"set_speed": "set-fan-speed", "set_power": "set-power-status"},
    }

    def __init__(self, serial: str, client: aiohttp.ClientSession) -> None:
        """Create an instance of MolekuleDevice."""
        self.serial = serial
        self._client = client

    async def turn_off(self):
        """Turn the device off."""
        await self._rpc_attr(self.state_keys["action"]["set_power"], self.state_keys["power_command"]["off"])

    async def turn_on(self):
        """Turn the device on."""
        await self._rpc_attr(self.state_keys["action"]["set_power"], self.state_keys["power_command"]["on"])

    async def smart(self):
        """Set device in auto mode."""
        await self._rpc_attr(self.state_keys["mode"]["smart"])

    async def manual(self):
        """Set device in manual mode."""
        await self._rpc_attr(self.state_keys["mode"]["manual"])

    # async def plasmawave_off(self):
    #     """Turn plasmawave off."""
    #     await self._rpc_attr(
    #         self.category_keys["plasma"], self.state_keys["plasma"]["off"]
    #     )

    # async def plasmawave_on(self):
    #     """Turn plasmawave on."""
    #     await self._rpc_attr(
    #         self.category_keys["plasma"], self.state_keys["plasma"]["on"]
    #     )

    async def airflow_1(self):
        """Set speed low."""
        await self._rpc_attr(self.state_keys["action"]["set_speed"], self.state_keys["fan_speed"]["1"])
    
    async def airflow_2(self):
        """Set speed low."""
        await self._rpc_attr(self.state_keys["action"]["set_speed"], self.state_keys["fan_speed"]["2"])

    async def airflow_3(self):
        """Set speed low."""
        await self._rpc_attr(self.state_keys["action"]["set_speed"], self.state_keys["fan_speed"]["3"])

    async def airflow_4(self):
        """Set speed low."""
        await self._rpc_attr(self.state_keys["action"]["set_speed"], self.state_keys["fan_speed"]["4"])

    async def airflow_5(self):
        """Set speed low."""
        await self._rpc_attr(self.state_keys["action"]["set_speed"], self.state_keys["fan_speed"]["5"])
    
    async def airflow_6(self):
        """Set speed low."""
        await self._rpc_attr(self.state_keys["action"]["set_speed"], self.state_keys["fan_speed"]["6"])

    # async def medium(self):
    #     """Set speed medium."""
    #     await self._rpc_attr(
    #         self.category_keys["airflow"], self.state_keys["airflow"]["medium"]
    #     )

    # async def high(self):
    #     """Set speed high."""
    #     await self._rpc_attr(
    #         self.category_keys["airflow"], self.state_keys["airflow"]["high"]
    #     )

    # async def turbo(self):
    #     """Set speed turbo."""
    #     await self._rpc_attr(
    #         self.category_keys["airflow"], self.state_keys["airflow"]["turbo"]
    #     )

    # async def sleep(self):
    #     """Set device in sleep mode."""
    #     await self._rpc_attr(
    #         self.category_keys["airflow"], self.state_keys["airflow"]["sleep"]
    #     )

    async def _rpc_attr(self, action: str, payload: str):
        _LOGGER.debug("_rpc_attr, action=%s, payload=%s", action, payload)
        resp = await self._client.post(
            self.CTRL_URL.format(serial=self.serial, action=action),
            data=payload,
            raise_for_status=True,
        )
        raw_resp = await resp.text()
        _LOGGER.debug("_rpc_attr response=%s", raw_resp)

    async def get_filter_life(self) -> int | None:
        """Get the total filter life."""
        response = await self._client.get(
            #self.STATE_URL.format(serial=self.serial)
            self.STATE_URL.format()
        )
        json = await response.json()

        # pylint: disable=pointless-string-statement
        """
        {
            'statusCode': 200, 'headers': {'resultCode': 'S100', 'resultMessage': ''},
            'body': {
                'deviceId': '847207352CE0_364yr8i989', 'totalCnt': 1,
                'data': [
                    {
                        'apiNo': 'A240', 'apiGroup': '004', 'modelId': 'C545', 'attributes': {'P01': '6480'}
                    }
                ]
            }
        }
        """

        try:
            content = json['content']
            for index, value in enumerate(content):
                serial_number = value['serialNumber']
                if serial_number == self.serial:
                    peco_filter = value['pecoFilter']
                if peco_filter:
                    return peco_filter
        except Exception:  # pylint: disable=broad-except
            return None

    async def get_state(self) -> dict[str, str]:
        """Get device state."""

        # All devices seem to have max 9 months filter life so don't need to call this API.
        # await self.get_filter_life()

        response = await self._client.get(
            self.STATE_URL.format()
        )
        json = await response.json()

        # pylint: disable=pointless-string-statement
        """
        {
            'statusCode': 200,
            'headers': {'resultCode': 'S100', 'resultMessage': ''},
            'body': {
                'deviceId': '847207352CE0_364yr8i989', 'totalCnt': 1,
                'data': [
                    {
                        'apiNo': 'A210', 'apiGroup': '001', 'deviceGroup': 'Air01', 'modelId': 'C545',
                        'attributes': {'A02': '0', 'A03': '01', 'A04': '01', 'A05': '01', 'A07': '0', 'A21': '1257', 'S07': '01', 'S08': '74', 'S14': '121'},
                        'rssi': '-55', 'creationTime': 1673449200634, 'utcDatetime': '2023-01-11 15:00:00', 'utcTimestamp': 1673449200
                    }
                ]
            }
        }
        """

        output = {}

        try:
            _LOGGER.debug(json)
            payload = json.json()['content']
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error parsing response json, received %s", json, exc_info=err
            )
            return output
            # Return empty object so that callers don't crash (#37)
        
        for index, value in enumerate(payload):
            _LOGGER.debug(f"Purifier {index + 1}: {json.dumps(value, indent=2)} \n")
            serial_number = value['serialNumber']
            subproduct_name = value['subProduct']['name']
            mac_address = value['macAddress']
            peco_filter = value['pecoFilter']
            fan_speed = value['fanspeed']
            mode = value['mode']
            online = value['online']
            aqi = value['aqi']
            silent = value['silent']

            output  =   {
                "serial_number": serial_number,
                "subproduct_name": subproduct_name,
                "mac_address": mac_address,
                "peco_filter": peco_filter,
                "fan_speed": fan_speed,
                "mode": mode,
                "online": online ,
                "aqi": aqi,
                "silent": silent
            }

        return output
