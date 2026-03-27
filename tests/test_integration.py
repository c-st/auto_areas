"""Integration tests for auto_areas using real HA instance."""

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.auto_areas.const import DOMAIN


@pytest.mark.asyncio
async def test_cover_group_is_created(
    hass: HomeAssistant,
    test_area: ar.AreaEntry,
    cover_entity: str,
    config_entry: MockConfigEntry,
):
    """Test that cover group is created when cover entity is assigned to area."""
    await hass.async_block_till_done()

    state = hass.states.get("cover.area_covers_test_room")
    assert state is not None, "Cover group entity should be created"


@pytest.mark.asyncio
async def test_binary_sensors_excluded_from_cover_group(
    hass: HomeAssistant,
    test_area: ar.AreaEntry,
    cover_entity: str,
    binary_sensor_door: str,
    config_entry: MockConfigEntry,
):
    """Test that binary_sensor with device_class 'door' is NOT in cover group.

    Regression test: appliances like Miele washing machines create
    binary_sensor entities with device_class "door" (contact sensors).
    These should not appear in cover groups.
    """
    await hass.async_block_till_done()

    state = hass.states.get("cover.area_covers_test_room")
    assert state is not None, "Cover group entity should be created"

    # Verify the cover entity is in the group
    entity_ids = state.attributes.get("entity_id", [])
    assert cover_entity in entity_ids, "Cover entity should be in group"
    assert (
        binary_sensor_door not in entity_ids
    ), "Binary sensor with door device_class should NOT be in cover group"


@pytest.mark.asyncio
async def test_presence_sensor_is_created(
    hass: HomeAssistant,
    test_area: ar.AreaEntry,
    config_entry: MockConfigEntry,
):
    """Test that presence binary sensor is created for the area."""
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.area_presence_test_room")
    assert state is not None, "Presence sensor entity should be created"


@pytest.mark.asyncio
async def test_light_group_is_created(
    hass: HomeAssistant,
    test_area: ar.AreaEntry,
    light_entity: str,
    config_entry: MockConfigEntry,
):
    """Test that light group is created when light entity is assigned to area."""
    await hass.async_block_till_done()

    state = hass.states.get("light.area_lights_test_room")
    assert state is not None, "Light group entity should be created"

    entity_ids = state.attributes.get("entity_id", [])
    assert light_entity in entity_ids, "Light entity should be in group"


@pytest.mark.asyncio
async def test_config_entry_unloads_cleanly(
    hass: HomeAssistant,
    test_area: ar.AreaEntry,
    cover_entity: str,
    light_entity: str,
    config_entry: MockConfigEntry,
):
    """Test that unloading config entry removes auto-created entities."""
    from homeassistant.const import STATE_UNAVAILABLE

    await hass.async_block_till_done()

    # Verify entities exist before unload
    assert (
        hass.states.get("cover.area_covers_test_room") is not None
    ), "Cover group should exist before unload"
    assert (
        hass.states.get("light.area_lights_test_room") is not None
    ), "Light group should exist before unload"
    assert (
        hass.states.get("binary_sensor.area_presence_test_room") is not None
    ), "Presence sensor should exist before unload"

    # Unload the config entry
    result = await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert result is True, "Config entry should unload successfully"

    # Verify entities are unavailable after unload (HA keeps state history)
    cover_state = hass.states.get("cover.area_covers_test_room")
    assert (
        cover_state is None or cover_state.state == STATE_UNAVAILABLE
    ), "Cover group should be unavailable after unload"

    light_state = hass.states.get("light.area_lights_test_room")
    assert (
        light_state is None or light_state.state == STATE_UNAVAILABLE
    ), "Light group should be unavailable after unload"

    presence_state = hass.states.get("binary_sensor.area_presence_test_room")
    assert (
        presence_state is None or presence_state.state == STATE_UNAVAILABLE
    ), "Presence sensor should be unavailable after unload"

    # Verify domain data is cleaned up
    assert (
        config_entry.entry_id not in hass.data.get(DOMAIN, {})
    ), "Entry should be removed from domain data"
