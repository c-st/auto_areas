"""An AutoArea"""
import logging

from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry
from homeassistant.helpers.device_registry import DeviceRegistry

_LOGGER = logging.getLogger(__name__)


class AutoArea(object):
    """An area managed by AutoAreas"""

    def __init__(self, hass: HomeAssistant, area: AreaEntry) -> None:
        self.hass = hass
        self.area_name = area.name
        self.area_id = area.id
        self.entities = []

        # Schedule initialization of entities for this area:
        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize
            )

    async def initialize(self) -> None:
        """Register relevant entities for this area"""
        _LOGGER.info("AutoArea %s", self.area_name)
        entity_registry: EntityRegistry = (
            await self.hass.helpers.entity_registry.async_get_registry()
        )
        device_registry: DeviceRegistry = (
            await self.hass.helpers.device_registry.async_get_registry()
        )

        # Collect entities for this area
        for _entity_id, entity in entity_registry.entities.items():
            # _LOGGER.debug("Evaluating entity %s", entity_id)
            if not is_valid(entity):
                continue

            if not get_area_id(entity, device_registry) == self.area_id:
                continue

            self.entities.append(entity)

        for entity in self.entities:
            _LOGGER.info("- Entity %s ", entity.entity_id)

        return


def is_valid(entity: RegistryEntry) -> bool:
    """Checks whether an entity should be included"""
    if entity.disabled:
        return False

    return True


def get_area_id(
    entity: RegistryEntry, device_registry: DeviceRegistry
) -> Optional[str]:
    """Determines area_id from a registry entry"""
    # Check entity_id of entity:
    if entity.area_id is not None:
        return entity.area_id

    # Check area of device from device registry
    if entity.device_id is not None:
        device = device_registry.devices[entity.device_id]
        if device is not None:
            return device.area_id

    return None
