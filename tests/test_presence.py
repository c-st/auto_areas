"""Tests for PresenceBinarySensor."""

import pytest
from unittest.mock import MagicMock, patch


# HA state constants
STATE_ON = "on"
STATE_OFF = "off"
STATE_HOME = "home"


def _make_state(entity_id, state_value):
    """Create a mock HA State object."""
    state = MagicMock()
    state.entity_id = entity_id
    state.state = state_value
    return state


def _make_event(entity_id, old_state_value, new_state_value):
    """Create a mock state change event."""
    old_state = _make_state(entity_id, old_state_value) if old_state_value else None
    new_state = _make_state(entity_id, new_state_value) if new_state_value else None

    event = MagicMock()
    event.data = {
        "entity_id": entity_id,
        "old_state": old_state,
        "new_state": new_state,
    }
    return event


def _make_auto_area(area_name="living_room", entry_id="test_entry"):
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = area_name
    auto_area.slugified_area_name = area_name
    auto_area.config_entry.entry_id = entry_id
    auto_area.config_entry.options = {}
    auto_area.device_info = {
        "identifiers": {("auto_areas", entry_id)},
        "name": "Auto Areas",
    }
    auto_area.get_valid_entities.return_value = []
    return auto_area


def _make_hass(states_map=None):
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    states_map = states_map or {}

    def get_state(entity_id):
        if entity_id in states_map:
            return _make_state(entity_id, states_map[entity_id])
        return None

    hass.states.get = MagicMock(side_effect=get_state)
    return hass


def _create_presence_sensor(hass, auto_area, entity_ids):
    """Create a PresenceBinarySensor with mocked dependencies."""
    from custom_components.auto_areas.binary_sensors.presence import (
        PresenceBinarySensor,
    )

    with patch.object(
        PresenceBinarySensor, '_get_sensor_entities',
        return_value=entity_ids,
    ):
        sensor = PresenceBinarySensor(hass=hass, auto_area=auto_area)
    return sensor


class TestPresenceDetection:
    """Test presence is True when any entity is in an ON state."""

    @pytest.mark.asyncio
    async def test_presence_true_when_entity_on(self):
        """Presence should be True when any tracked entity transitions to ON."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_presence_sensor(
            hass, auto_area,
            ["binary_sensor.motion1", "binary_sensor.motion2"],
        )
        sensor.presence = False

        event = _make_event("binary_sensor.motion1", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.presence is True

    @pytest.mark.asyncio
    async def test_presence_true_with_home_state(self):
        """Presence should be True when entity transitions to HOME state."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_presence_sensor(
            hass, auto_area,
            ["binary_sensor.motion1"],
        )
        sensor.presence = False

        event = _make_event("binary_sensor.motion1", STATE_OFF, STATE_HOME)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.presence is True


class TestPresenceClears:
    """Test presence clears when all entities leave ON states."""

    @pytest.mark.asyncio
    async def test_presence_clears_when_all_off(self):
        """Presence should clear when all entities go to OFF."""
        auto_area = _make_auto_area()
        entity_ids = [
            "switch.area_presence_lock_living_room",
            "binary_sensor.motion1",
            "binary_sensor.motion2",
        ]
        # All entities are off
        hass = _make_hass({
            "binary_sensor.motion1": STATE_OFF,
            "binary_sensor.motion2": STATE_OFF,
            "switch.area_presence_lock_living_room": STATE_OFF,
        })

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.presence is False

    @pytest.mark.asyncio
    async def test_presence_stays_when_one_still_on(self):
        """Presence should remain True when at least one entity is still ON."""
        auto_area = _make_auto_area()
        entity_ids = [
            "switch.area_presence_lock_living_room",
            "binary_sensor.motion1",
            "binary_sensor.motion2",
        ]
        # motion2 is still on
        hass = _make_hass({
            "binary_sensor.motion1": STATE_OFF,
            "binary_sensor.motion2": STATE_ON,
            "switch.area_presence_lock_living_room": STATE_OFF,
        })

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.presence is True
