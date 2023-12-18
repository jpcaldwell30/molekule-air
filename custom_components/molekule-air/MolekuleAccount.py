import dataclasses
from binascii import crc32
import requests
from molekule import Molekule
import aiohttp
import logging
import json

@dataclasses.dataclass
class MolekuleDeviceStub:
    serial_number: str
    mac: str
    alias: str

_LOGGER = logging.getLogger(__name__)

class MolekuleAccount:
    def __init__(self, access_token: str, user_username: str, user_password: str):
        self.access_token = access_token
        self.user_username = user_username
        self.user_password = user_password

    def check_access_token(self):
        session = aiohttp.ClientSession()
        auth = Molekule(websession=session, host="https://api.molekule.com/users/me")
        resp = auth.request(method="get", username=self.user_username, password=self.user_password, path="devices")
        if resp.status_code != 200:
            raise Exception(
                f"Error while performing RPC checkAccessToken ({resp.status_code}): {resp.json()}"
            )
        

    def get_device_info_list(self):
        session = aiohttp.ClientSession()
        auth = Molekule(websession=session, host="https://api.molekule.com/users/me")
        resp = auth.request(method="get", username=self.user_username, password=self.user_password, path="devices")
        if resp.status_code != 200:
            raise Exception(
                f"Error while performing RPC checkAccessToken ({resp.status_code}): {resp.text}"
            )
            #content = resp.json()['content']
        return [
            MolekuleDeviceStub(
                serial_number=d["serialNumber"],
                mac=d["macAddress"],
                alias=d['subProduct']['name'],
            )
            for d in resp.json()["content"]
            #for index, value in enumerate(content):
        ]
