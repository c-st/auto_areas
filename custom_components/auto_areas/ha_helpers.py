"""Collection of utility methods for dealing with HomeAssistant."""

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry


def get_all_entities(
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    area_id: str,
    domains: list[str] | None = None,
) -> list[RegistryEntry]:
    """Return all entities from an area.

    Resolved through the registries' indexed area lookups, so the cost scales
    with the size of the area instead of the size of the whole registry.

    This runs once per auto entity per area, so a full-registry walk here is not
    merely slow: it blocks the event loop long enough that Home Assistant never
    finishes starting on a large install. See
    tests/test_ha_helpers.py::TestGetAllEntitiesScaling.
    """
    if domains is None:
        # Preserved from the original implementation: no domains, no matches.
        return []

    entities: list[RegistryEntry] = []
    seen: set[str] = set()

    # Entities assigned to the area directly.
    for entity in er.async_entries_for_area(entity_registry, area_id):
        seen.add(entity.entity_id)
        if entity.domain in domains:
            entities.append(entity)

    # Entities that inherit the area from their device. An entity that carries
    # its own area_id has already been handled above and must not be pulled in
    # via its device, because the entity's own area wins.
    for device in dr.async_entries_for_area(device_registry, area_id):
        for entity in er.async_entries_for_device(
            entity_registry, device.id, include_disabled_entities=True
        ):
            if entity.entity_id in seen or entity.area_id is not None:
                continue
            seen.add(entity.entity_id)
            if entity.domain in domains:
                entities.append(entity)

    return entities


def get_area_id(
    entity: RegistryEntry, device_registry: DeviceRegistry
) -> str | None:
    """Get area_id from a registry entry."""

    # Defined directly at entity
    if entity.area_id is not None:
        return entity.area_id

    # Inherited from device
    if entity.device_id is not None:
        device = device_registry.async_get(entity.device_id)
        if device is not None:
            return device.area_id

    return None


def all_states_are_off(
    hass: HomeAssistant,
    presence_indicating_entity_ids: list[str],
    on_states: list[str],
) -> bool:
    """Make sure that none of the entities is in any on state."""
    all_states = [
        hass.states.get(entity_id) for entity_id in presence_indicating_entity_ids
    ]
    return all(state.state not in on_states for state in filter(None, all_states))


def is_valid_entity(hass: HomeAssistant, entity: RegistryEntry) -> bool:
    """Check whether an entity should be included."""
    if entity.disabled:
        return False

    entity_state = hass.states.get(entity.entity_id)
    if entity_state and entity_state.state == STATE_UNAVAILABLE:
        return False

    return True
