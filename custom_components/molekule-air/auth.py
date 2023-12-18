from dataclasses import dataclass
import boto3

import boto3
from botocore import UNSIGNED
from botocore.client import Config


from pycognito import Cognito as AWS

COGNITO_APP_CLIENT_ID = "1ec4fa3oriciupg94ugoi84kkk"
COGNITO_CLIENT_SECRET_KEY = "k554d4pvgf2n0chbhgtmbe4q0ul4a9flp3pcl6a47ch6rripvvr"
COGNITO_USER_POOL_ID = "us-west-2_KqrEZKC6r"

@dataclass
class MolekuleAuthResponse:
    access_token: str
    pool_id: str
    client_id: str
    user: AWS

def login(username: str, password: str, **kwargs):
    """Generate fresh credentials"""
    """Get Access Token"""
    MolekuleAuthResponse.pool_id = kwargs.get("pool_id", COGNITO_USER_POOL_ID)
    MolekuleAuthResponse.client_id = kwargs.get("client_id", COGNITO_APP_CLIENT_ID)

    user = AWS(
        pool_id=MolekuleAuthResponse.pool_id, 
        client_id=MolekuleAuthResponse.client_id, 
        username=username
    )

    user.authenticate(password=password)
    MolekuleAuthResponse.user = user
    MolekuleAuthResponse.access_token = user.access_token
    return MolekuleAuthResponse


def refresh():
    """Refresh credentials"""
    MolekuleAuthResponse.user.check_token()
    MolekuleAuthResponse.access_token = MolekuleAuthResponse.user.access_token
    return MolekuleAuthResponse


