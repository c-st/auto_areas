"""
AutoArea
Has a set of managed entities assigned to the same area.
"""
import logging
from typing import Set

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry

from custom_components.auto_areas.auto_lights import AutoLights
from custom_components.auto_areas.const import AUTO_AREAS_RELEVANT_DOMAINS
from custom_components.auto_areas.ha_helpers import get_all_entities

_LOGGER = logging.getLogger(__name__)


class AutoArea(object):
    """An area managed by AutoAreas"""

    def __init__(self, hass: HomeAssistant, area: AreaEntry, config: dict) -> None:
        self.hass: HomeAssistant = hass
        self.area = area
        self.area_name = area.name
        self.area_id = area.id
        self.config = config.get(area.normalized_name, {})
        self.entities: Set[RegistryEntry] = set()

        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize()
            )

    async def initialize(self) -> None:
        """Register relevant entities for this area"""
        _LOGGER.info("AutoArea '%s' (config %s)", self.area_name, self.config)

        entity_registry: EntityRegistry = (
            await self.hass.helpers.entity_registry.async_get_registry()
        )
        device_registry: DeviceRegistry = (
            await self.hass.helpers.device_registry.async_get_registry()
        )

        # Collect entities for this area
        entities = get_all_entities(
            entity_registry, device_registry, self.area_id, AUTO_AREAS_RELEVANT_DOMAINS
        )
        self.entities = [entity for entity in entities if self.is_valid_entity(entity)]

        # Setup AutoLights
        self.auto_lights = AutoLights(self.hass, self.entities, self.area, self.config)

        for entity in self.entities:
            _LOGGER.info(
                "- Entity %s (device_class: %s)",
                entity.entity_id,
                entity.device_class or entity.original_device_class,
            )

    def is_valid_entity(self, entity: RegistryEntry) -> bool:
        """Checks whether an entity should be included"""
        if entity.disabled:
            return False

        entity_state = self.hass.states.get(entity.entity_id)
        if entity_state and entity_state.state == STATE_UNAVAILABLE:
            return False

        return True
