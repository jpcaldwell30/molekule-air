"""Constants for the Molekule Air integration."""
from typing import Final

DOMAIN = "molekule-air"
MOLEKULE_NAME: Final = "Molekule Air"
CONF_PASSWORD: Final = "password"
CONF_USERNAME: Final = "username"
MOLEKULE_API_BASE_URL: Final = "https://api.molekule.com/users/me"
TIMEOUT: Final = 10.0

COGNITO_APP_CLIENT_ID: Final = "1ec4fa3oriciupg94ugoi84kkk"
COGNITO_USER_POOL_ID: Final = "us-west-2_KqrEZKC6r"

MODE_MANUAL: Final = "manual"
MODE_SMART: Final = "smart"
PRESET_MODES: Final = [MODE_SMART, MODE_MANUAL]
