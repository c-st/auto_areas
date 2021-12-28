import logging
from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaRegistry
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.auto_areas.auto_presence import AutoPresenceBinarySensor
from custom_components.auto_areas.const import RELEVANT_DOMAINS
from custom_components.auto_areas.ha_helpers import get_all_entities

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Set up all binary_sensors"""
    _LOGGER.info("Setup AutoPresence platform")

    area_registry: AreaRegistry = await hass.helpers.area_registry.async_get_registry()
    entity_registry: EntityRegistry = (
        await hass.helpers.entity_registry.async_get_registry()
    )
    device_registry: DeviceRegistry = (
        await hass.helpers.device_registry.async_get_registry()
    )

    # Setup area presence sensors
    presence_sensors: List[Entity] = []
    for area in area_registry.async_list_areas():
        area_entities = get_all_entities(
            entity_registry, device_registry, area.id, RELEVANT_DOMAINS
        )
        presence_sensors.append(AutoPresenceBinarySensor(hass, area_entities, area))

    async_add_entities(presence_sensors)
