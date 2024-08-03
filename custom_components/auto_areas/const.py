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
from homeassistant.components.group.const import DOMAIN as GROUP_DOMAIN
from homeassistant.components.switch.const import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.const import STATE_HOME, STATE_ON, STATE_PLAYING


LOGGER: Logger = getLogger(__package__)

NAME = "Auto Areas"
DOMAIN = "auto_areas"
VERSION = "2.7.0"

#
# Naming constants
#
ISSUE_TYPE_YAML_DETECTED = "issue_yaml_detected"
ISSUE_TYPE_INVALID_AREA = "invalid_area_config"
#
PRESENCE_LOCK_SWITCH_PREFIX = "Area Presence Lock "
PRESENCE_LOCK_SWITCH_ENTITY_PREFIX = "switch.area_presence_lock_"

SLEEP_MODE_SWITCH_PREFIX = "Area Sleep Mode "
SLEEP_MODE_SWITCH_ENTITY_PREFIX = "switch.area_sleep_mode_"

PRESENCE_BINARY_SENSOR_PREFIX = "Area Presence "
PRESENCE_BINARY_SENSOR_ENTITY_PREFIX = "binary_sensor.area_presence_"

ILLUMINANCE_SENSOR_PREFIX = "Area Illuminance "
ILLUMINANCE_SENSOR_ENTITY_PREFIX = "sensor.area_illuminance_"

TEMPERATURE_SENSOR_PREFIX = "Area Temperature "
TEMPERATURE_SENSOR_ENTITY_PREFIX = "sensor.area_temperature_"

HUMIDITY_SENSOR_PREFIX = "Area Humidity "
HUMIDITY_SENSOR_ENTITY_PREFIX = "sensor.area_humidity_"

COVER_GROUP_PREFIX = "Area Covers "
COVER_GROUP_ENTITY_PREFIX = "cover.area_covers_"

LIGHT_GROUP_PREFIX = "Area Lights "
LIGHT_GROUP_ENTITY_PREFIX = "light.area_lights_"
#
# Config flow constants
#
CONFIG_AREA = "area"
CONFIG_IS_SLEEPING_AREA = "is_sleeping_area"
CONFIG_EXCLUDED_LIGHT_ENTITIES = "excluded_light_entities"
CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE = "auto_lights_illuminance_threshold"
CONFIG_HUMIDITY_CALCULATION = "humidity_calculation"
CONFIG_TEMPERATURE_CALCULATION = "temperature_calculation"
CONFIG_ILLUMINANCE_CALCULATION = "illuminance_calculation"


# Fetch entities from these domains:
RELEVANT_DOMAINS = [
    BINARY_SENSOR_DOMAIN,
    SENSOR_DOMAIN,
    SWITCH_DOMAIN,
    LIGHT_DOMAIN,
    COVER_DOMAIN,
]

EXCLUDED_DOMAINS = [
    DOMAIN,
    GROUP_DOMAIN,
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
