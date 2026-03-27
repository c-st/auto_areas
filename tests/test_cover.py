"""Tests for cover group entity filtering."""

import pytest
from unittest.mock import MagicMock

from custom_components.auto_areas.ha_helpers import get_all_entities


def _make_entity(entity_id, domain, device_class=None, area_id=None, device_id=None):
    """Create a mock RegistryEntry."""
    entity = MagicMock()
    entity.entity_id = entity_id
    entity.domain = domain
    entity.device_class = device_class
    entity.original_device_class = device_class
    entity.area_id = area_id
    entity.device_id = device_id
    entity.disabled = False
    return entity


def _make_registries(entities, area_id="test_area"):
    """Create mock entity and device registries."""
    entity_registry = MagicMock()
    entity_registry.entities = {e.entity_id: e for e in entities}
    device_registry = MagicMock()
    # All entities are assigned to area directly
    for e in entities:
        if e.area_id is None:
            e.area_id = area_id
    return entity_registry, device_registry


@pytest.mark.asyncio
async def test_cover_group_excludes_binary_sensor_with_door_device_class():
    """Binary sensors with device_class 'door' must not appear in cover groups.

    Regression test: appliances like Miele washing machines create
    binary_sensor entities with device_class "door" (contact sensors).
    These share device_class values with cover entities but are not covers.
    """
    area_id = "kitchen"
    entities = [
        _make_entity("cover.kitchen_blinds", "cover", "blind", area_id=area_id),
        _make_entity(
            "binary_sensor.washing_machine_door",
            "binary_sensor",
            "door",
            area_id=area_id,
        ),
        _make_entity(
            "binary_sensor.window_contact",
            "binary_sensor",
            "window",
            area_id=area_id,
        ),
        _make_entity("cover.kitchen_shutter", "cover", "shutter", area_id=area_id),
    ]
    entity_registry, device_registry = _make_registries(entities, area_id)

    result = get_all_entities(entity_registry, device_registry, area_id, domains=["cover"])

    result_ids = [e.entity_id for e in result]
    assert "cover.kitchen_blinds" in result_ids
    assert "cover.kitchen_shutter" in result_ids
    assert "binary_sensor.washing_machine_door" not in result_ids
    assert "binary_sensor.window_contact" not in result_ids
    assert len(result) == 2


@pytest.mark.asyncio
async def test_cover_group_empty_when_no_covers():
    """When an area has no cover entities, the result should be empty."""
    area_id = "laundry"
    entities = [
        _make_entity(
            "binary_sensor.dryer_door", "binary_sensor", "door", area_id=area_id
        ),
    ]
    entity_registry, device_registry = _make_registries(entities, area_id)

    result = get_all_entities(entity_registry, device_registry, area_id, domains=["cover"])

    assert result == []
