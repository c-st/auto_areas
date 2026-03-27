"""Tests for AutoEntity state aggregation."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# HA state constants (avoid top-level HA import for environments without HA installed)
STATE_UNKNOWN = "unknown"
STATE_UNAVAILABLE = "unavailable"


def _make_state(entity_id, state_value, last_updated=None):
    """Create a mock HA State object."""
    state = MagicMock()
    state.entity_id = entity_id
    state.state = state_value
    state.last_updated = last_updated or datetime.now(tz=timezone.utc)
    return state


def _make_event(entity_id, old_state, new_state):
    """Create a mock state change event."""
    event = MagicMock()
    event.data = {
        "entity_id": entity_id,
        "old_state": old_state,
        "new_state": new_state,
    }
    return event


def _make_auto_area(area_name="test_area", entry_id="test_entry"):
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


def _make_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    return hass


def _create_auto_entity(hass, auto_area):
    """Create an AutoEntity with mocked dependencies."""
    from custom_components.auto_areas.auto_entity import AutoEntity
    from homeassistant.components.sensor.const import SensorDeviceClass

    with patch.object(AutoEntity, '_get_sensor_entities', return_value=[]):
        entity = AutoEntity(
            hass=hass,
            auto_area=auto_area,
            device_class=SensorDeviceClass.TEMPERATURE,
            name_prefix="Area Temperature ",
            prefix="sensor.area_temperature_",
        )
    return entity


class TestAutoEntityStateAggregation:
    """Test state aggregation with numeric values."""

    def test_entity_states_stored_correctly(self):
        """Numeric states are stored without mutating the original state."""
        hass = _make_hass()
        auto_area = _make_auto_area()
        entity = _create_auto_entity(hass, auto_area)

        state1 = _make_state("sensor.temp1", "21.5")
        state2 = _make_state("sensor.temp2", "22.3")

        entity.entity_states["sensor.temp1"] = state1
        entity.entity_states["sensor.temp2"] = state2
        entity.entity_float_values["sensor.temp1"] = 21.5
        entity.entity_float_values["sensor.temp2"] = 22.3

        assert len(entity.entity_states) == 2
        assert entity.entity_float_values["sensor.temp1"] == 21.5
        assert entity.entity_float_values["sensor.temp2"] == 22.3


class TestAutoEntityUnknownUnavailable:
    """Test handling of UNKNOWN/UNAVAILABLE states."""

    @pytest.mark.asyncio
    async def test_unknown_state_excluded(self):
        """UNKNOWN states should be excluded from entity_states."""
        hass = _make_hass()
        auto_area = _make_auto_area()
        entity = _create_auto_entity(hass, auto_area)

        # Add a valid state first
        valid_state = _make_state("sensor.temp1", "21.5")
        entity.entity_states["sensor.temp1"] = valid_state
        entity.entity_float_values["sensor.temp1"] = 21.5

        # Simulate UNKNOWN state change
        unknown_state = _make_state("sensor.temp1", STATE_UNKNOWN)
        event = _make_event("sensor.temp1", valid_state, unknown_state)

        with patch.object(entity, 'async_write_ha_state'):
            await entity._handle_state_change(event)

        assert "sensor.temp1" not in entity.entity_states
        assert "sensor.temp1" not in entity.entity_float_values

    @pytest.mark.asyncio
    async def test_unavailable_state_excluded(self):
        """UNAVAILABLE states should be excluded from entity_states."""
        hass = _make_hass()
        auto_area = _make_auto_area()
        entity = _create_auto_entity(hass, auto_area)

        valid_state = _make_state("sensor.temp1", "21.5")
        entity.entity_states["sensor.temp1"] = valid_state

        unavailable_state = _make_state("sensor.temp1", STATE_UNAVAILABLE)
        event = _make_event("sensor.temp1", valid_state, unavailable_state)

        with patch.object(entity, 'async_write_ha_state'):
            await entity._handle_state_change(event)

        assert "sensor.temp1" not in entity.entity_states


class TestAutoEntityStateMutation:
    """Test that the state mutation bug is fixed."""

    @pytest.mark.asyncio
    async def test_original_state_not_mutated(self):
        """The original HA State object should not be modified by _handle_state_change."""
        hass = _make_hass()
        auto_area = _make_auto_area()
        entity = _create_auto_entity(hass, auto_area)

        new_state = _make_state("sensor.temp1", "23.7")
        original_state_value = new_state.state  # Should remain "23.7" (string)

        event = _make_event("sensor.temp1", None, new_state)

        with patch.object(entity, 'async_write_ha_state'):
            await entity._handle_state_change(event)

        # The original state object should NOT have been mutated to a float
        assert new_state.state == original_state_value
        assert isinstance(new_state.state, str)

        # But the float value should be stored separately
        assert entity.entity_float_values["sensor.temp1"] == 23.7

    @pytest.mark.asyncio
    async def test_none_new_state_handled_gracefully(self):
        """_handle_state_change should return early when new_state is None."""
        hass = _make_hass()
        auto_area = _make_auto_area()
        entity = _create_auto_entity(hass, auto_area)

        entity.entity_states["sensor.temp1"] = _make_state("sensor.temp1", "21.0")
        entity.entity_float_values["sensor.temp1"] = 21.0

        event = _make_event("sensor.temp1", _make_state("sensor.temp1", "21.0"), None)

        with patch.object(entity, 'async_write_ha_state'):
            await entity._handle_state_change(event)

        assert "sensor.temp1" in entity.entity_states
        assert entity.entity_float_values["sensor.temp1"] == 21.0

    @pytest.mark.asyncio
    async def test_non_numeric_state_excluded(self):
        """Non-numeric state values should be excluded."""
        hass = _make_hass()
        auto_area = _make_auto_area()
        entity = _create_auto_entity(hass, auto_area)

        # Pre-populate with a valid state
        entity.entity_states["sensor.temp1"] = _make_state("sensor.temp1", "21.0")
        entity.entity_float_values["sensor.temp1"] = 21.0

        # Send a non-numeric state
        bad_state = _make_state("sensor.temp1", "not_a_number")
        event = _make_event("sensor.temp1", None, bad_state)

        with patch.object(entity, 'async_write_ha_state'):
            await entity._handle_state_change(event)

        assert "sensor.temp1" not in entity.entity_states
        assert "sensor.temp1" not in entity.entity_float_values


class TestAutoEntityAsyncAddedToHass:
    """Test async_added_to_hass loading initial states."""

    @pytest.mark.asyncio
    async def test_loads_initial_states(self):
        """async_added_to_hass should load initial states from hass."""
        hass = _make_hass()
        auto_area = _make_auto_area()

        from custom_components.auto_areas.auto_entity import AutoEntity
        from homeassistant.components.sensor.const import SensorDeviceClass

        with patch.object(AutoEntity, '_get_sensor_entities',
                          return_value=["sensor.temp1", "sensor.temp2"]):
            entity = AutoEntity(
                hass=hass,
                auto_area=auto_area,
                device_class=SensorDeviceClass.TEMPERATURE,
                name_prefix="Area Temperature ",
                prefix="sensor.area_temperature_",
            )

        state1 = _make_state("sensor.temp1", "21.0")
        state2 = _make_state("sensor.temp2", "22.5")
        hass.states.get = MagicMock(side_effect=lambda eid: {
            "sensor.temp1": state1,
            "sensor.temp2": state2,
        }.get(eid))

        with patch.object(entity, 'async_write_ha_state'), \
             patch('custom_components.auto_areas.auto_entity.async_track_state_change_event'):
            await entity.async_added_to_hass()

        assert "sensor.temp1" in entity.entity_states
        assert "sensor.temp2" in entity.entity_states
