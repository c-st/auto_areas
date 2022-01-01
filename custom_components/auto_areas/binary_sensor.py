import logging
from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaRegistry
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.auto_areas.presence_binary_sensor import (
    PresenceBinarySensor,
)
from custom_components.auto_areas.const import AUTO_AREAS_RELEVANT_DOMAINS
from custom_components.auto_areas.ha_helpers import get_all_entities

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Set up all binary_sensors"""
    area_registry: AreaRegistry = await hass.helpers.area_registry.async_get_registry()
    entity_registry: EntityRegistry = (
        await hass.helpers.entity_registry.async_get_registry()
    )
    device_registry: DeviceRegistry = (
        await hass.helpers.device_registry.async_get_registry()
    )

    binary_sensor_entities = []
    for area in area_registry.async_list_areas():
        area_entities: List[Entity] = get_all_entities(
            entity_registry, device_registry, area.id, AUTO_AREAS_RELEVANT_DOMAINS
        )
        binary_sensor_entities.append(PresenceBinarySensor(hass, area_entities, area))

    async_add_entities(binary_sensor_entities)
