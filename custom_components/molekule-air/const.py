"""Constants for the Molekule Air Purifier component."""

from enum import Enum, unique
from typing import Final

MOLEKULE_DOMAIN: Final = "molekule-air"

MOLEKULE_NAME: Final = "Molekule Air Purifier"
MOLEKULE_DATA_KEY: Final = "fan_molekule_air_purifier"
MOLEKULE_DATA_COORDINATOR: Final = "coordinator"
MOLEKULE_AUTH_RESPONSE: Final = "MolekuleAuthResponse"
MOLEKULE_ACCESS_TOKEN_EXPIRATION: Final = "access_token_expiration"

ATTR_AIRFLOW: Final = "fanspeed"
ATTR_AIR_AQI: Final = "aqi"
ATTR_FILTER_LIFE: Final = "pecoFilter"
ATTR_AIR_QUALITY: Final = "air_quality"
ATTR_AIR_QVALUE: Final = "air_qvalue"
#ATTR_FILTER_HOUR: Final = "filter_hour"
#ATTR_FILTER_REPLACEMENT_DATE: Final = "filter_replace_date"
#ATTR_LOCATION: Final = "location"
ATTR_MODE: Final = "mode"
#ATTR_PLASMA: Final = "plasma"
ATTR_POWER: Final = "power"

SENSOR_AIR_QVALUE: Final = "air_qvalue"
SENSOR_AQI: Final = "aqi"
SENSOR_FILTER_LIFE: Final = "pecoFilter"

OFF_VALUE: Final = "off"
ON_VALUE: Final = "on"

# airflow can contain the special preset values of manual and sleep
# but we are not using those as fan speed.
# AIRFLOW_LOW: Final = "low"
# AIRFLOW_MEDIUM: Final = "medium"
# AIRFLOW_HIGH: Final = "high"
# AIRFLOW_TURBO: Final = "turbo"
# AIRFLOW_SLEEP: Final = "sleep"

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

# mode can contain the special preset value of manual.
#MODE_STANDBY: Final = "standby" #off
#MODE_AUTOPROTECT: Final = "autoprotect" #auto?
#MODE_AUTO: Final = "auto"
MODE_MANUAL: Final = "manual"
MODE_SMART: Final = "smart"
#MODE_AUTOPROTECT_STANDARD: Final = "autoprotectstandard"
#MODE_AUTOPROTECT_QUIET: Final = "autoprotectquiet"
#PRESET_MODE_AUTOPROTECT_STANDARD: Final = "Auto Protect Standard"
#PRESET_MODE_AUTOPROTECT_QUIET: Final = "Auto Protect Quiet"
#PRESET_MODE_AUTOPROTECT: Final = "Auto protect"
PRESET_MODE_MANUAL: Final = "Manual"
PRESET_MODE_SMART: Final = "Smart"
PRESET_MODES: Final = [
    # PRESET_MODE_AUTOPROTECT_STANDARD,
    # PRESET_MODE_AUTOPROTECT_QUIET,
    # PRESET_MODE_AUTOPROTECT,
    PRESET_MODE_SMART,
    PRESET_MODE_MANUAL,
]

# SERVICES: Final = [
#     SERVICE_PLASMAWAVE_ON,
#     SERVICE_PLASMAWAVE_OFF,
#     SERVICE_PLASMAWAVE_TOGGLE,
# ]

@unique
class NumericPresetModes(str, Enum):
    """Alternate numeric preset modes.

    The value correspond to the index in PRESET_MODES.
    """

    PRESET_MODE_SMART = "1"
    #PRESET_MODE_AUTO_PLASMA_OFF = "2"
    PRESET_MODE_MANUAL = "2"
    #PRESET_MODE_MANUAL_PLASMA_OFF = "4"
    #PRESET_MODE_SLEEP = "5"
