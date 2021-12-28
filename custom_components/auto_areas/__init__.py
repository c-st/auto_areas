"""AutoAreas custom_component for Home Assistant"""
import logging
from typing import MutableMapping

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaRegistry
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.helpers import discovery

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.ha_helpers import set_data

from .const import DATA_AUTO_AREA, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup integration (YAML-based)"""

    # Load config
    conf: dict = config.get(DOMAIN) or {}
    _LOGGER.debug("Found config %s", conf)

    area_registry: AreaRegistry = await hass.helpers.area_registry.async_get_registry()

    # Initialize and store areas
    auto_areas: MutableMapping[str, AutoArea] = {}

    for area in area_registry.async_list_areas():
        auto_areas[area.id] = AutoArea(hass, area)

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
