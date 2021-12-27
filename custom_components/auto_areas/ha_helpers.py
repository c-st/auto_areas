"""Collection of utility methods for dealing with HomeAssistant"""
from typing import List, Optional
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry
from homeassistant.helpers.device_registry import DeviceRegistry


def get_all_entities(
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    area_id: str,
    domains: List[str] = None,
) -> List:
    """Returns all entities from an area"""
    entities = []

    for _entity_id, entity in entity_registry.entities.items():
        if not get_area_id(entity, device_registry) == area_id:
            continue

        if entity.domain not in domains:
            continue

        entities.append(entity)

    return entities


def get_area_id(
    entity: RegistryEntry, device_registry: DeviceRegistry
) -> Optional[str]:
    """Determines area_id from a registry entry"""

    # Defined directly at entity
    if entity.area_id is not None:
        return entity.area_id

    # Inherited from device
    if entity.device_id is not None:
        device = device_registry.devices[entity.device_id]
        if device is not None:
            return device.area_id

    return None
