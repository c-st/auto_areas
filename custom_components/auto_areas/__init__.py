"""AutoAreas custom_component for Home Assistant"""
import logging

from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.area_registry import AreaRegistry

from custom_components.auto_areas.auto_area import AutoArea

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration using YAML"""
    # Load config
    conf = config.get(DOMAIN) or {}
    _LOGGER.debug("Found config %s", conf)

    # Initialize areas
    area_registry: AreaRegistry = await hass.helpers.area_registry.async_get_registry()

    auto_areas = {}
    for area in area_registry.async_list_areas():
        auto_areas[area.id] = AutoArea(hass, area)

    hass.data[DOMAIN] = auto_areas
    return True
