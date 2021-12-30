"""AutoAreas custom_component for Home Assistant"""
import logging
from typing import MutableMapping

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.area_registry import AreaRegistry
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
from voluptuous.error import MultipleInvalid
from voluptuous.schema_builder import PREVENT_EXTRA, REMOVE_EXTRA

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.ha_helpers import set_data

from .const import DATA_AUTO_AREA, DOMAIN

_LOGGER = logging.getLogger(__name__)

area_config_schema = vol.Schema({"is_sleeping_area": bool}, extra=PREVENT_EXTRA)
config_schema = vol.Schema({str: {"is_sleeping_area": bool}})


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

    area_registry: AreaRegistry = await hass.helpers.area_registry.async_get_registry()

    auto_areas: MutableMapping[str, AutoArea] = {}

    for area in area_registry.async_list_areas():
        auto_areas[area.id] = AutoArea(hass, area, auto_areas_config)

    set_data(hass, DATA_AUTO_AREA, auto_areas)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            component=BINARY_SENSOR_DOMAIN,  # un-intuitive but correct
            platform=DOMAIN,
            discovered={},
            hass_config={"foo": "bar"},  # should not be an empty dict
        )
    )

    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    return


async def async_unload_entry(hass, entry):
    return
