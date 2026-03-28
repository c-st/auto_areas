"""Tests for OpenBinarySensor."""

import pytest
from unittest.mock import MagicMock, patch


# HA state constants
STATE_ON = "on"
STATE_OFF = "off"
STATE_UNKNOWN = "unknown"
STATE_UNAVAILABLE = "unavailable"


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


def _make_auto_area(area_name="kitchen", entry_id="test_entry"):
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


def _create_open_sensor(hass, auto_area, entity_ids):
    """Create an OpenBinarySensor with mocked dependencies."""
    from custom_components.auto_areas.binary_sensors.open import (
        OpenBinarySensor,
    )

    with patch.object(
        OpenBinarySensor, '_get_sensor_entities',
        return_value=entity_ids,
    ):
        sensor = OpenBinarySensor(hass=hass, auto_area=auto_area)
    return sensor


class TestOpenNoSensors:
    """Test behavior when no open/closed sensors exist."""

    def test_no_sensors_state_is_off(self):
        """With no sensors, aggregate state should be off (fail-safe)."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_open_sensor(hass, auto_area, [])
        sensor.any_open = False

        assert sensor.state == STATE_OFF

    def test_no_sensors_initial_any_open_false(self):
        """With no sensors, _any_sensor_on returns False."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_open_sensor(hass, auto_area, [])
        assert sensor._any_sensor_on() is False


class TestOpenSingleSensor:
    """Test with a single door sensor."""

    def test_single_door_sensor_on(self):
        """Single door sensor ON (open) should set aggregate to on."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_ON,
        })

        sensor = _create_open_sensor(
            hass, auto_area, ["binary_sensor.door_kitchen"],
        )
        assert sensor._any_sensor_on() is True

    def test_single_door_sensor_off(self):
        """Single door sensor OFF (closed) should set aggregate to off."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(
            hass, auto_area, ["binary_sensor.door_kitchen"],
        )
        assert sensor._any_sensor_on() is False


class TestOpenOrLogic:
    """Test OR aggregation logic with multiple sensors."""

    @pytest.mark.asyncio
    async def test_one_sensor_on_aggregate_on(self):
        """If any one sensor is ON, aggregate should be ON."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
            "binary_sensor.window_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(
            hass, auto_area,
            ["binary_sensor.door_kitchen", "binary_sensor.window_kitchen"],
        )
        sensor.any_open = False

        event = _make_event("binary_sensor.door_kitchen", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is True

    @pytest.mark.asyncio
    async def test_all_sensors_off_aggregate_off(self):
        """If all sensors are OFF, aggregate should be OFF."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.door_kitchen",
            "binary_sensor.window_kitchen",
            "binary_sensor.opening_kitchen",
        ]
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
            "binary_sensor.window_kitchen": STATE_OFF,
            "binary_sensor.opening_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(hass, auto_area, entity_ids)
        sensor.any_open = True

        event = _make_event("binary_sensor.door_kitchen", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is False

    @pytest.mark.asyncio
    async def test_stays_on_when_one_still_on(self):
        """Open stays True when at least one sensor is still ON."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.door_kitchen",
            "binary_sensor.window_kitchen",
        ]
        # window is still open
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
            "binary_sensor.window_kitchen": STATE_ON,
        })

        sensor = _create_open_sensor(hass, auto_area, entity_ids)
        sensor.any_open = True

        event = _make_event("binary_sensor.door_kitchen", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is True


class TestOpenUnavailable:
    """Test handling of unavailable/unknown states."""

    @pytest.mark.asyncio
    async def test_sensor_becomes_unavailable(self):
        """Unavailable sensor excluded, remaining sensors determine state."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.door_kitchen",
            "binary_sensor.window_kitchen",
        ]
        # window is off, door is going unavailable
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_UNAVAILABLE,
            "binary_sensor.window_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(hass, auto_area, entity_ids)
        sensor.any_open = True

        event = _make_event("binary_sensor.door_kitchen", STATE_ON, STATE_UNAVAILABLE)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is False

    @pytest.mark.asyncio
    async def test_all_sensors_unavailable(self):
        """All sensors unavailable → state is off (fail-safe)."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.door_kitchen",
            "binary_sensor.window_kitchen",
        ]
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_UNAVAILABLE,
            "binary_sensor.window_kitchen": STATE_UNAVAILABLE,
        })

        sensor = _create_open_sensor(hass, auto_area, entity_ids)
        sensor.any_open = True

        event = _make_event("binary_sensor.window_kitchen", STATE_ON, STATE_UNAVAILABLE)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is False

    @pytest.mark.asyncio
    async def test_sensor_becomes_unknown(self):
        """Unknown sensor excluded, remaining sensors determine state."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.door_kitchen",
            "binary_sensor.window_kitchen",
        ]
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_UNKNOWN,
            "binary_sensor.window_kitchen": STATE_ON,
        })

        sensor = _create_open_sensor(hass, auto_area, entity_ids)
        sensor.any_open = True

        event = _make_event("binary_sensor.door_kitchen", STATE_ON, STATE_UNKNOWN)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        # window_kitchen is still ON, so open stays
        assert sensor.any_open is True


class TestOpenMixedDeviceClasses:
    """Test with mixed device classes (door + window + opening)."""

    def test_mixed_classes_one_on(self):
        """Mixed device classes — one ON triggers aggregate."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
            "binary_sensor.window_kitchen": STATE_ON,
            "binary_sensor.opening_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(
            hass, auto_area,
            [
                "binary_sensor.door_kitchen",
                "binary_sensor.window_kitchen",
                "binary_sensor.opening_kitchen",
            ],
        )
        assert sensor._any_sensor_on() is True

    def test_mixed_classes_all_off(self):
        """Mixed device classes — all OFF means closed."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
            "binary_sensor.window_kitchen": STATE_OFF,
            "binary_sensor.opening_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(
            hass, auto_area,
            [
                "binary_sensor.door_kitchen",
                "binary_sensor.window_kitchen",
                "binary_sensor.opening_kitchen",
            ],
        )
        assert sensor._any_sensor_on() is False


class TestOpenStateChanges:
    """Test state transitions update aggregate correctly."""

    @pytest.mark.asyncio
    async def test_off_to_on_transition(self):
        """Sensor going from off to on (closed to open) triggers open state."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_open_sensor(
            hass, auto_area, ["binary_sensor.door_kitchen"],
        )
        sensor.any_open = False

        event = _make_event("binary_sensor.door_kitchen", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is True

    @pytest.mark.asyncio
    async def test_on_to_off_transition(self):
        """Sensor going from on to off (open to closed) clears open state when no others open."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.door_kitchen": STATE_OFF,
        })

        sensor = _create_open_sensor(
            hass, auto_area, ["binary_sensor.door_kitchen"],
        )
        sensor.any_open = True

        event = _make_event("binary_sensor.door_kitchen", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is False


class TestOpenEntityProperties:
    """Test entity naming and device class."""

    def test_unique_id(self):
        """unique_id should follow the expected pattern."""
        auto_area = _make_auto_area(entry_id="my_entry_123")
        hass = _make_hass()

        sensor = _create_open_sensor(hass, auto_area, [])
        assert sensor.unique_id == "my_entry_123_aggregated_open"

    def test_device_class(self):
        """Device class should be OPENING."""
        from homeassistant.components.binary_sensor import BinarySensorDeviceClass
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_open_sensor(hass, auto_area, [])
        assert sensor.device_class == BinarySensorDeviceClass.OPENING


class TestOpenEdgeCases:
    """Test edge cases in open detection."""

    @pytest.mark.asyncio
    async def test_no_change_transition_ignored(self):
        """Open should ignore events where old == new state."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_open_sensor(
            hass, auto_area, ["binary_sensor.door_kitchen"],
        )
        sensor.any_open = False

        event = _make_event("binary_sensor.door_kitchen", STATE_OFF, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.any_open is False

    @pytest.mark.asyncio
    async def test_none_new_state_handled_gracefully(self):
        """Handle None new_state without crashing."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_open_sensor(
            hass, auto_area, ["binary_sensor.door_kitchen"],
        )
        sensor.any_open = True

        event = _make_event("binary_sensor.door_kitchen", STATE_ON, None)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)
