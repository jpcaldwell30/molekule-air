from aiohttp import ClientSession, ClientResponse
from .molekule_aws_auth import Auth_AWS
from datetime import date

class Auth:
    """Class to make authenticated requests."""

    def __init__(self, websession: ClientSession, host: str,):
        """Initialize the auth."""
        self.websession = websession
        self.host = host

    async def request(self, method: str, path: str, **kwargs) -> ClientResponse:
        """Make a request."""
        auth = Auth_AWS(username="username", password="password")
        headers = kwargs.get("headers")

        if headers is None:
            headers = {}
        else:
            headers = dict(headers)
        await auth._get_access_token()
        headers["authorization"] = auth.access_token
        headers["x-api-version"] = '1.0'
        headers['host'] = 'api.molekule.com'
        headers['content-type'] = 'application/json'
        headers['Date']= date.today().strftime("%a, %d %b %Y %H:%M:%S GMT")
        return await self.websession.request(
            method, f"{self.host}/{path}", **kwargs, headers=headers,
        )