"""Constants for the Molekule Air integration."""

from enum import Enum, unique
from typing import Final

DOMAIN = "molekule_air"
MOLEKULE_NAME: Final = "Molekule Air"
ICON = "mdi:format-quote-close"
SENSOR = "sensor"
MOLEKULE_DATA_COORDINATOR: Final = "coordinator"
MOLEKULE_AUTH_RESPONSE: Final = "MolekuleAuthResponse"
CONF_PASSWORD: Final = "password"
CONF_USERNAME: Final = "username"
MOLEKULE_ACCESS_TOKEN_EXPIRATION: Final = "access_token_expiration"
MOLEKCULE_SUGGESTED_HOST: Final = "https://api.molekule.com/users/me"
ATTRIBUTION = "Data provided by https://api.molekule.com/"
TIMEOUT = 5.00

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
AIRFLOW_1: Final = "1"
AIRFLOW_2: Final = "2"
AIRFLOW_3: Final = "3"
AIRFLOW_4: Final = "4"
AIRFLOW_5: Final = "5"
AIRFLOW_6: Final = "6"

ORDERED_NAMED_FAN_SPEEDS: Final = [
    AIRFLOW_1,
    AIRFLOW_2,
    AIRFLOW_3,
    AIRFLOW_4,
    AIRFLOW_5,
    AIRFLOW_6,
]

MODE_MANUAL: Final = "manual"
MODE_SMART: Final = "smart"
PRESET_MODE_MANUAL: Final = "Manual"
PRESET_MODE_SMART: Final = "Smart"
PRESET_MODES: Final = [
    PRESET_MODE_SMART,
    PRESET_MODE_MANUAL,
]


@unique
class NumericPresetModes(str, Enum):
    """Alternate numeric preset modes.
    The value correspond to the index in PRESET_MODES.
    """

    PRESET_MODE_SMART = "1"
    PRESET_MODE_MANUAL = "2"
