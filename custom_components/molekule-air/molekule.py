from molekule_aws_auth import Auth_AWS
import requests
from aiohttp import ClientSession, ClientResponse
from datetime import date

class Molekule:
    def __init__(self, websession: ClientSession, host: str):
       self.host = host
       self.websession = websession
    async def request(self,
            method: str, 
            path: str,
            username: str,
            password: str, 
            **kwargs
    ) -> ClientResponse:
        headers = kwargs.get("headers")
        user = username
        users_pass = password
        """Make a request."""
        auth = Auth_AWS(username=user, password=users_pass)
        await auth._get_access_token()
        
        if headers is None:
             headers = {}
        else:
             headers = dict(headers)
        headers['authorization'] = auth.access_token
        headers["x-api-version"] = '1.0'
        headers['host'] = 'api.molekule.com'
        headers['accept'] = 'application/json'
        headers['content-type'] = 'application/json'
        headers['user-agent'] = 'Molekule/3.1.3 (com.molekule.ios; build:1167; iOS 14.0.0) Alamofire/4.9.1'
        headers['Date'] = date.today().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        return requests.request(
            method, f"{self.host}/{path}", **kwargs, headers=headers,
        )