"""Python Client that get the AWS access_token from AWS for your Molekule Account"""
from pycognito import Cognito as AWS

class Auth_AWS:
    """Molekule AWS Authentication Class"""
    access_token = None
    def __init__ (
        self,
        # AWS Credentials (Should Be left alone unless you know what you are doing)
        client_id: str = '1ec4fa3oriciupg94ugoi84kkk',
        user_pool: str = 'us-west-2_KqrEZKC6r',
        username: str = '',
        password: str = '',
    ):
        self.user_pool = user_pool
        self.client_id = client_id
        self.username = username
        self.password = password

    async def _get_access_token(self) -> str:
        """Get User Input"""
        username = self.username
        password = self.password
        """Get Access Token"""
        u = AWS(self.user_pool, self.client_id, username=username)
        """Test Input"""
        try:
            # Recieve Access Token from AWS (Cognito Python Library)
            u.authenticate(password=password)
            #print(u.access_token)
            #Print Access Token
            # set global variable to access_token
            Auth_AWS.access_token = u.access_token
        except Exception as e:
            """Guess that the issues is a Invaid password"""
            print("Invalid Credentials")
            """Print Error"""
            print(e)