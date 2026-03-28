"""Constants for the Molekule Air integration."""
from typing import Final

DOMAIN = "molekule-air"
MOLEKULE_NAME: Final = "Molekule Air"
MOLEKULE_DATA_COORDINATOR: Final = "coordinator"
CONF_PASSWORD: Final = "password"
CONF_USERNAME: Final = "username"
MOLEKULE_API_BASE_URL: Final = "https://api.molekule.com/users/me"
ATTRIBUTION: Final = "Data provided by https://api.molekule.com/"
TIMEOUT: Final = 10.0

COGNITO_APP_CLIENT_ID: Final = "1ec4fa3oriciupg94ugoi84kkk"
COGNITO_CLIENT_SECRET_KEY: Final = "k554d4pvgf2n0chbhgtmbe4q0ul4a9flp3pcl6a47ch6rripvvr"
COGNITO_USER_POOL_ID: Final = "us-west-2_KqrEZKC6r"

ATTR_AIRFLOW: Final = "fanspeed"
ATTR_AIR_AQI: Final = "aqi"
ATTR_FILTER_LIFE: Final = "pecoFilter"
ATTR_AIR_QUALITY: Final = "air_quality"
ATTR_AIR_QVALUE: Final = "air_qvalue"
ATTR_MODE: Final = "mode"
ATTR_POWER: Final = "power"

SENSOR_AIR_QVALUE: Final = "air_qvalue"
SENSOR_AQI: Final = "aqi"
SENSOR_FILTER_LIFE: Final = "pecoFilter"

OFF_VALUE: Final = "off"
ON_VALUE: Final = "on"

MODE_MANUAL: Final = "manual"
MODE_SMART: Final = "smart"
PRESET_MODES: Final = [MODE_SMART, MODE_MANUAL]
