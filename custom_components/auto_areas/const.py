"""Constants"""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OCCUPANCY,
    DEVICE_CLASS_PRESENCE,
    BinarySensorDeviceClass,
)
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

# from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import STATE_HOME, STATE_ON, STATE_PLAYING

NAME = "Auto Areas"
DOMAIN = "auto_areas"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ISSUE_URL = "https://github.com/custom-components/auto_areas/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Defaults
DEFAULT_NAME = DOMAIN
RELEVANT_DOMAINS = [BINARY_SENSOR_DOMAIN, SENSOR_DOMAIN, SWITCH_DOMAIN, LIGHT_DOMAIN]

DEVICE_CLASSES = [cls.value for cls in BinarySensorDeviceClass]
DEVICE_CLASS_DOMAINS = (BINARY_SENSOR_DOMAIN, SENSOR_DOMAIN)

# AutoAreas
DATA_AUTO_AREA = "auto-area"
DATA_AUTO_PRESENCE = "auto-presence"

# Presence

PRESENCE_BINARY_SENSOR_DEVICE_CLASSES = (
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OCCUPANCY,
    DEVICE_CLASS_PRESENCE,
)

PRESENCE_BINARY_SENSOR_STATES = [
    STATE_ON,
    STATE_HOME,
    STATE_PLAYING,
]
