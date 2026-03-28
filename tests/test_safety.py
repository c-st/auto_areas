"""Tests for SafetyBinarySensor."""

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


def _create_safety_sensor(hass, auto_area, entity_ids):
    """Create a SafetyBinarySensor with mocked dependencies."""
    from custom_components.auto_areas.binary_sensors.safety import (
        SafetyBinarySensor,
    )

    with patch.object(
        SafetyBinarySensor, '_get_sensor_entities',
        return_value=entity_ids,
    ):
        sensor = SafetyBinarySensor(hass=hass, auto_area=auto_area)
    return sensor


class TestSafetyNoSensors:
    """Test behavior when no safety sensors exist."""

    def test_no_sensors_state_is_off(self):
        """With no safety sensors, aggregate state should be off (fail-safe)."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_safety_sensor(hass, auto_area, [])
        sensor.safety_alert = False

        assert sensor.state == STATE_OFF

    def test_no_sensors_initial_alert_false(self):
        """With no safety sensors, _any_sensor_on returns False."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_safety_sensor(hass, auto_area, [])
        assert sensor._any_sensor_on() is False


class TestSafetySingleSensor:
    """Test with a single safety sensor."""

    def test_single_smoke_sensor_on(self):
        """Single smoke sensor ON should set aggregate to on."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_ON,
        })

        sensor = _create_safety_sensor(
            hass, auto_area, ["binary_sensor.smoke_kitchen"],
        )
        assert sensor._any_sensor_on() is True

    def test_single_smoke_sensor_off(self):
        """Single smoke sensor OFF should set aggregate to off."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(
            hass, auto_area, ["binary_sensor.smoke_kitchen"],
        )
        assert sensor._any_sensor_on() is False


class TestSafetyOrLogic:
    """Test OR aggregation logic with multiple sensors."""

    @pytest.mark.asyncio
    async def test_one_sensor_on_aggregate_on(self):
        """If any one sensor is ON, aggregate should be ON."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
            "binary_sensor.co_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(
            hass, auto_area,
            ["binary_sensor.smoke_kitchen", "binary_sensor.co_kitchen"],
        )
        sensor.safety_alert = False

        event = _make_event("binary_sensor.smoke_kitchen", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is True

    @pytest.mark.asyncio
    async def test_all_sensors_off_aggregate_off(self):
        """If all sensors are OFF, aggregate should be OFF."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.smoke_kitchen",
            "binary_sensor.co_kitchen",
            "binary_sensor.moisture_kitchen",
        ]
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
            "binary_sensor.co_kitchen": STATE_OFF,
            "binary_sensor.moisture_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(hass, auto_area, entity_ids)
        sensor.safety_alert = True

        event = _make_event("binary_sensor.smoke_kitchen", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is False

    @pytest.mark.asyncio
    async def test_stays_on_when_one_still_on(self):
        """Alert stays True when at least one sensor is still ON."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.smoke_kitchen",
            "binary_sensor.co_kitchen",
        ]
        # co sensor is still on
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
            "binary_sensor.co_kitchen": STATE_ON,
        })

        sensor = _create_safety_sensor(hass, auto_area, entity_ids)
        sensor.safety_alert = True

        event = _make_event("binary_sensor.smoke_kitchen", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is True


class TestSafetyUnavailable:
    """Test handling of unavailable/unknown states."""

    @pytest.mark.asyncio
    async def test_sensor_becomes_unavailable(self):
        """Unavailable sensor excluded, remaining sensors determine state."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.smoke_kitchen",
            "binary_sensor.co_kitchen",
        ]
        # co sensor is off, smoke is going unavailable
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_UNAVAILABLE,
            "binary_sensor.co_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(hass, auto_area, entity_ids)
        sensor.safety_alert = True

        event = _make_event("binary_sensor.smoke_kitchen", STATE_ON, STATE_UNAVAILABLE)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is False

    @pytest.mark.asyncio
    async def test_all_sensors_unavailable(self):
        """All sensors unavailable → state is off (fail-safe)."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.smoke_kitchen",
            "binary_sensor.co_kitchen",
        ]
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_UNAVAILABLE,
            "binary_sensor.co_kitchen": STATE_UNAVAILABLE,
        })

        sensor = _create_safety_sensor(hass, auto_area, entity_ids)
        sensor.safety_alert = True

        event = _make_event("binary_sensor.co_kitchen", STATE_ON, STATE_UNAVAILABLE)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is False

    @pytest.mark.asyncio
    async def test_sensor_becomes_unknown(self):
        """Unknown sensor excluded, remaining sensors determine state."""
        auto_area = _make_auto_area()
        entity_ids = [
            "binary_sensor.smoke_kitchen",
            "binary_sensor.co_kitchen",
        ]
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_UNKNOWN,
            "binary_sensor.co_kitchen": STATE_ON,
        })

        sensor = _create_safety_sensor(hass, auto_area, entity_ids)
        sensor.safety_alert = True

        event = _make_event("binary_sensor.smoke_kitchen", STATE_ON, STATE_UNKNOWN)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        # co_kitchen is still ON, so alert stays
        assert sensor.safety_alert is True


class TestSafetyMixedDeviceClasses:
    """Test with mixed device classes (smoke + moisture + CO)."""

    def test_mixed_classes_one_on(self):
        """Mixed device classes — one ON triggers aggregate."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
            "binary_sensor.moisture_kitchen": STATE_ON,
            "binary_sensor.co_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(
            hass, auto_area,
            [
                "binary_sensor.smoke_kitchen",
                "binary_sensor.moisture_kitchen",
                "binary_sensor.co_kitchen",
            ],
        )
        assert sensor._any_sensor_on() is True

    def test_mixed_classes_all_off(self):
        """Mixed device classes — all OFF means safe."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
            "binary_sensor.moisture_kitchen": STATE_OFF,
            "binary_sensor.co_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(
            hass, auto_area,
            [
                "binary_sensor.smoke_kitchen",
                "binary_sensor.moisture_kitchen",
                "binary_sensor.co_kitchen",
            ],
        )
        assert sensor._any_sensor_on() is False


class TestSafetyStateChanges:
    """Test state transitions update aggregate correctly."""

    @pytest.mark.asyncio
    async def test_off_to_on_transition(self):
        """Sensor going from off to on triggers alert."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_safety_sensor(
            hass, auto_area, ["binary_sensor.smoke_kitchen"],
        )
        sensor.safety_alert = False

        event = _make_event("binary_sensor.smoke_kitchen", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is True

    @pytest.mark.asyncio
    async def test_on_to_off_transition(self):
        """Sensor going from on to off clears alert when no others on."""
        auto_area = _make_auto_area()
        hass = _make_hass({
            "binary_sensor.smoke_kitchen": STATE_OFF,
        })

        sensor = _create_safety_sensor(
            hass, auto_area, ["binary_sensor.smoke_kitchen"],
        )
        sensor.safety_alert = True

        event = _make_event("binary_sensor.smoke_kitchen", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is False


class TestSafetyEntityProperties:
    """Test entity naming and device class."""

    def test_unique_id(self):
        """unique_id should follow the expected pattern."""
        auto_area = _make_auto_area(entry_id="my_entry_123")
        hass = _make_hass()

        sensor = _create_safety_sensor(hass, auto_area, [])
        assert sensor.unique_id == "my_entry_123_aggregated_safety"

    def test_device_class(self):
        """Device class should be SAFETY."""
        from homeassistant.components.binary_sensor import BinarySensorDeviceClass
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_safety_sensor(hass, auto_area, [])
        assert sensor.device_class == BinarySensorDeviceClass.SAFETY


class TestSafetyEdgeCases:
    """Test edge cases in safety detection."""

    @pytest.mark.asyncio
    async def test_no_change_transition_ignored(self):
        """Safety should ignore events where old == new state."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_safety_sensor(
            hass, auto_area, ["binary_sensor.smoke_kitchen"],
        )
        sensor.safety_alert = False

        event = _make_event("binary_sensor.smoke_kitchen", STATE_OFF, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.safety_alert is False

    @pytest.mark.asyncio
    async def test_none_new_state_handled_gracefully(self):
        """Handle None new_state without crashing."""
        auto_area = _make_auto_area()
        hass = _make_hass()

        sensor = _create_safety_sensor(
            hass, auto_area, ["binary_sensor.smoke_kitchen"],
        )
        sensor.safety_alert = True

        event = _make_event("binary_sensor.smoke_kitchen", STATE_ON, None)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)
