"""Constants for Auto Areas."""
from logging import Logger, getLogger
from numbers import Number
from statistics import mean, median

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch.const import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import STATE_HOME, STATE_ON, STATE_PLAYING, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import State
from homeassistant.helpers.typing import StateType

LOGGER: Logger = getLogger(__package__)

NAME = "Auto Areas"
DOMAIN = "auto_areas"
VERSION = "2.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

#
# Constants
#

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

CALCULATE_MAX = "max"
CALCULATE_MIN = "min"
CALCULATE_MEAN = "mean"
CALCULATE_MEDIAN = "median"
CALCULATE_LAST = "last"
CALCULATE_ALL = "all"
CALCULATE_ONE = "one"
CALCULATE_NONE = "none"

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


def calculate_max(values: list[State]) -> StateType:
    """Calculate the maximum of the list of values."""
    calc_values = [v.state for v in values if isinstance(v, Number) and not isinstance(v.state, bool) and not isinstance(v.state, str)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return max(calc_values)

def calculate_min(values: list[State]) -> StateType:
    """Calculate the mean of the list of values."""
    calc_values = [v.state for v in values if isinstance(v, Number) and not isinstance(v.state, bool) and not isinstance(v.state, str)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return min(calc_values)

def calculate_mean(values: list[State]) -> StateType:
    """Calculate the mean of the list of values."""
    calc_values = [v.state for v in values if isinstance(v, Number) and not isinstance(v.state, bool) and not isinstance(v.state, str)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return mean(calc_values)

def calculate_median(values: list[State]) -> StateType:
    """Calculate the median of the list of values."""
    calc_values = [v.state for v in values if isinstance(v, Number) and not isinstance(v.state, bool) and not isinstance(v.state, str)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return median(calc_values)

def calculate_all(values: list[State]) -> StateType:
    """Calculate the whether all of the list of values are true."""
    calc_values = [v.state for v in values if isinstance(v.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if not v]) == 0

def calculate_one(values: list[State]) -> StateType:
    """Calculate the whether one of the list of values is true."""
    calc_values = [v.state for v in values if isinstance(v.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if v]) > 0

def calculate_none(values: list[State]) -> StateType:
    """Calculate the whether none of the list of values is true."""
    calc_values = [v.state for v in values if isinstance(v.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if v]) == 0

def calculate_last(values: list[State]) -> StateType:
    """Calculate the last update of the list of values."""
    calc_values = [v for v in values if v.state is not None and v.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return sorted(calc_values, key=lambda v: v.last_updated, reverse=True)[0].state

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
