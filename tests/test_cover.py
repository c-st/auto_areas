"""Tests for cover group entity filtering."""

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.auto_areas.ha_helpers import get_all_entities


def _add_entity(entity_registry, domain, unique_id, area_id, device_class=None):
    """Register an entity in an area."""
    entry = entity_registry.async_get_or_create(
        domain=domain,
        platform="test",
        unique_id=unique_id,
        original_device_class=device_class,
    )
    return entity_registry.async_update_entity(entry.entity_id, area_id=area_id)


async def test_cover_group_excludes_binary_sensor_with_door_device_class(hass):
    """Binary sensors with device_class 'door' must not appear in cover groups.

    Regression test: appliances like Miele washing machines create
    binary_sensor entities with device_class "door" (contact sensors).
    These share device_class values with cover entities but are not covers.
    """
    area_registry = ar.async_get(hass)
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    area = area_registry.async_create("Kitchen")

    blinds = _add_entity(entity_registry, "cover", "kitchen_blinds", area.id, "blind")
    shutter = _add_entity(
        entity_registry, "cover", "kitchen_shutter", area.id, "shutter"
    )
    washing_machine_door = _add_entity(
        entity_registry, "binary_sensor", "washing_machine_door", area.id, "door"
    )
    window_contact = _add_entity(
        entity_registry, "binary_sensor", "window_contact", area.id, "window"
    )

    result = get_all_entities(
        entity_registry, device_registry, area.id, domains=["cover"]
    )

    result_ids = [e.entity_id for e in result]
    assert blinds.entity_id in result_ids
    assert shutter.entity_id in result_ids
    assert washing_machine_door.entity_id not in result_ids
    assert window_contact.entity_id not in result_ids
    assert len(result) == 2


async def test_cover_group_empty_when_no_covers(hass):
    """When an area has no cover entities, the result should be empty."""
    area_registry = ar.async_get(hass)
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    area = area_registry.async_create("Laundry")

    _add_entity(entity_registry, "binary_sensor", "dryer_door", area.id, "door")

    result = get_all_entities(
        entity_registry, device_registry, area.id, domains=["cover"]
    )

    assert result == []
