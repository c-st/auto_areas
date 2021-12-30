import logging
from typing import Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.auto_presence import AutoPresenceBinarySensor
from custom_components.auto_areas.const import DATA_AUTO_AREA
from custom_components.auto_areas.ha_helpers import get_data

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Set up all binary_sensors"""
    _LOGGER.info("Setup binary_sensor platform")

    # Setup area presence sensors
    entities: List[Entity] = []
    auto_areas: Dict[AutoArea] = get_data(hass, DATA_AUTO_AREA)

    for auto_area in auto_areas.values():
        entities.append(AutoPresenceBinarySensor(hass, auto_area.entities, auto_area))

    async_add_entities(entities)
