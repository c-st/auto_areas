"""AutoAreas custom_component for Home Assistant"""
import logging
from typing import MutableMapping

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.area_registry import AreaRegistry
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
from voluptuous.error import MultipleInvalid
from voluptuous.schema_builder import PREVENT_EXTRA

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.ha_helpers import set_data

from .const import CONFIG_SLEEPING_AREA, CONFIG_PRESENCE_SCENE, CONFIG_GOODBYE_SCENE, CONFIG_SLEEPING_SCENE, DOMAIN, DOMAIN_DATA

# SUGGESTIONS:
#  - add binary_sensor.any_area_occupied that determines if ANY of the areas occupancy switches are on (device_class: presence)
#  - utilize some same entity names as MagicAreas to make transition back and forth easier (e.g. area_presence_hold_XXXX)
#  - utilize device to have all the auto_areas entities "related" together in the Home Assistant UI

_LOGGER = logging.getLogger(__name__)

area_config_schema = vol.Schema(
    {
        vol.Optional(CONFIG_SLEEPING_AREA): bool,
        vol.Optional(CONFIG_PRESENCE_SCENE): str,
        vol.Optional(CONFIG_GOODBYE_SCENE): str,
        vol.Optional(CONFIG_SLEEPING_SCENE): str
    }, extra=PREVENT_EXTRA)

config_schema = vol.Schema(
    {str: {
        vol.Optional(CONFIG_SLEEPING_AREA): bool,
        vol.Optional(CONFIG_PRESENCE_SCENE): str,
        vol.Optional(CONFIG_GOODBYE_SCENE): str,
        vol.Optional(CONFIG_SLEEPING_SCENE): str
    }})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup integration (YAML-based)"""

    # Load and validate config
    auto_areas_config: dict = config.get(DOMAIN) or {}
    try:
        config_schema(auto_areas_config)
    except MultipleInvalid as exception:
        _LOGGER.error(
            "Configuration is invalid (validation message: '%s'). Config: %s",
            exception.error_message,
            auto_areas_config,
        )
        return False

    _LOGGER.debug("Found config %s", auto_areas_config)

    area_registry: AreaRegistry = hass.helpers.area_registry.async_get(hass)

    auto_areas: MutableMapping[str, AutoArea] = {}

    for area in area_registry.async_list_areas():
        auto_areas[area.id] = AutoArea(hass, area, auto_areas_config)

    set_data(hass, DOMAIN_DATA, auto_areas)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            component=BINARY_SENSOR_DOMAIN,  # un-intuitive but correct
            platform=DOMAIN,
            discovered={},
            hass_config={"nonempty": "dict"},  # should not be an empty dict
        )
    )

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            component=SWITCH_DOMAIN,
            platform=DOMAIN,
            discovered={},
            hass_config={"nonempty": "dict"},
        )
    )

    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    return


async def async_unload_entry(hass, entry):
    return
