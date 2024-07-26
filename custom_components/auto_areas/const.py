"""Constants for Auto Areas."""
from logging import Logger, getLogger

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch.const import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import STATE_HOME, STATE_ON, STATE_PLAYING

from .calculations import (
    calculate_all,
    calculate_last,
    calculate_max,
    calculate_mean,
    calculate_median,
    calculate_min,
    calculate_none,
    calculate_one
)


LOGGER: Logger = getLogger(__package__)

NAME = "Auto Areas"
DOMAIN = "auto_areas"
VERSION = "2.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

#
# Constants
#
ISSUE_TYPE_YAML_DETECTED = "issue_yaml_detected"
#
PRESENCE_LOCK_SWITCH_PREFIX = "Area Presence Lock "
PRESENCE_LOCK_SWITCH_ENTITY_PREFIX = "switch.area_presence_lock_"

SLEEP_MODE_SWITCH_PREFIX = "Area Sleep Mode "
SLEEP_MODE_SWITCH_ENTITY_PREFIX = "switch.area_sleep_mode_"

PRESENCE_BINARY_SENSOR_PREFIX = "Area Presence "
PRESENCE_BINARY_SENSOR_ENTITY_PREFIX = "binary_sensor.area_presence_"

ILLUMINANCE_SENSOR_PREFIX = "Area Illuminance "
ILLUMINANCE_SENSOR_ENTITY_PREFIX = "sensor.area_illuminance_"
#
# Config constants
#
CONFIG_AREA = "area"
CONFIG_IS_SLEEPING_AREA = "is_sleeping_area"
CONFIG_EXCLUDED_LIGHT_ENTITIES = "excluded_light_entities"
CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE = "auto_lights_illuminance_threshold"
CONFIG_HUMIDITY_CALCULATION = "humidity_calculation"
CONFIG_TEMPERATURE_CALCULATION = "temperature_calculation"
CONFIG_ILLUMINANCE_CALCULATION = "illuminance_calculation"
CONFIG_OCCUPANCY_CALCULATION = "occupancy_calculation"

CALCULATE_MAX = "max"
CALCULATE_MIN = "min"
CALCULATE_MEAN = "mean"
CALCULATE_MEDIAN = "median"
CALCULATE_LAST = "last"
CALCULATE_ALL = "all"
CALCULATE_ONE = "one"
CALCULATE_NONE = "none"

CALCULATE = {
    CALCULATE_MAX: calculate_max,
    CALCULATE_MEAN: calculate_mean,
    CALCULATE_MIN: calculate_min,
    CALCULATE_MEDIAN: calculate_median,
    CALCULATE_ALL: calculate_all,
    CALCULATE_ONE: calculate_one,
    CALCULATE_NONE: calculate_none,
    CALCULATE_LAST: calculate_last,
}

#
# Config
#

# Fetch entities from these domains
RELEVANT_DOMAINS = [
    BINARY_SENSOR_DOMAIN,
    SENSOR_DOMAIN,
    SWITCH_DOMAIN,
    LIGHT_DOMAIN,
]

# Presence entities
PRESENCE_BINARY_SENSOR_DEVICE_CLASSES = (
    BinarySensorDeviceClass.MOTION,
    BinarySensorDeviceClass.OCCUPANCY,
    BinarySensorDeviceClass.PRESENCE,
)

# Presence states
PRESENCE_ON_STATES = [
    STATE_ON,
    STATE_HOME,
    STATE_PLAYING,
]
