"""Constants for Auto Areas."""
from logging import Logger, getLogger

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
)
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import STATE_HOME, STATE_ON, STATE_PLAYING


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
