"""Tests for PresenceBinarySensor timeout behaviour."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# HA state constants
STATE_ON = "on"
STATE_OFF = "off"


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


def _make_auto_area(area_name="living_room", entry_id="test_entry", presence_timeout=0):
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = area_name
    auto_area.slugified_area_name = area_name
    auto_area.config_entry.entry_id = entry_id
    auto_area.config_entry.options = {"presence_timeout": presence_timeout}
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


class TestTimeoutDisabled:
    """Test that timeout=0 preserves existing immediate-clear behaviour."""

    @pytest.mark.asyncio
    async def test_presence_clears_immediately_when_timeout_zero(self):
        """With timeout=0, presence clears immediately when all sensors go off."""
        auto_area = _make_auto_area(presence_timeout=0)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass({"binary_sensor.motion1": STATE_OFF})

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.presence is False
        assert sensor._timeout_cancel is None


class TestTimeoutEnabled:
    """Test that presence stays on during the timeout period."""

    @pytest.mark.asyncio
    async def test_presence_stays_on_after_sensor_clears(self):
        """With timeout>0, presence should remain True when sensor goes off."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass({"binary_sensor.motion1": STATE_OFF})

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch(
            'custom_components.auto_areas.binary_sensors.presence.async_call_later'
        ) as mock_call_later:
            mock_call_later.return_value = MagicMock()
            with patch.object(sensor, 'async_write_ha_state'):
                await sensor._handle_state_change(event)

        # Presence should still be True — waiting for timeout
        assert sensor.presence is True
        # async_call_later should have been called with 30s
        mock_call_later.assert_called_once()
        assert mock_call_later.call_args[0][1] == 30

    @pytest.mark.asyncio
    async def test_presence_on_immediately_when_sensor_triggers(self):
        """Presence should go on immediately regardless of timeout setting."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass()

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = False

        event = _make_event("binary_sensor.motion1", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        assert sensor.presence is True


class TestTimerReset:
    """Test that new sensor activity resets the timeout timer."""

    @pytest.mark.asyncio
    async def test_timer_cancelled_on_new_presence(self):
        """If a sensor fires during timeout, the pending timer is cancelled."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass()

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        # Simulate a pending timeout
        cancel_mock = MagicMock()
        sensor._timeout_cancel = cancel_mock

        # Sensor triggers again
        event = _make_event("binary_sensor.motion1", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(event)

        # Timer should have been cancelled
        cancel_mock.assert_called_once()
        assert sensor._timeout_cancel is None
        assert sensor.presence is True

    @pytest.mark.asyncio
    async def test_timer_resets_on_repeated_off(self):
        """When sensors go off again during a pending timeout, timer resets."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass({"binary_sensor.motion1": STATE_OFF})

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        # Simulate a pending timeout
        old_cancel = MagicMock()
        sensor._timeout_cancel = old_cancel

        event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch(
            'custom_components.auto_areas.binary_sensors.presence.async_call_later'
        ) as mock_call_later:
            new_cancel = MagicMock()
            mock_call_later.return_value = new_cancel
            with patch.object(sensor, 'async_write_ha_state'):
                await sensor._handle_state_change(event)

        # Old timer cancelled, new one started
        old_cancel.assert_called_once()
        mock_call_later.assert_called_once()


class TestTimeoutExpires:
    """Test that presence clears after timeout expires."""

    @pytest.mark.asyncio
    async def test_presence_clears_after_timeout(self):
        """After timeout callback fires, presence should clear if still all off."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass({"binary_sensor.motion1": STATE_OFF})

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_timeout(None)

        assert sensor.presence is False
        assert sensor._timeout_cancel is None

    @pytest.mark.asyncio
    async def test_timeout_does_not_clear_if_sensor_on(self):
        """If a sensor came back on before timeout fires, presence should stay."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        # Sensor came back on before the callback
        hass = _make_hass({"binary_sensor.motion1": STATE_ON})

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        with patch.object(sensor, 'async_write_ha_state') as mock_write:
            await sensor._handle_timeout(None)

        assert sensor.presence is True
        mock_write.assert_not_called()


class TestMultipleSensors:
    """Test timeout with multiple sensors."""

    @pytest.mark.asyncio
    async def test_timeout_starts_only_when_all_off(self):
        """Timeout should not start if some sensors are still on."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1", "binary_sensor.motion2"]
        # motion2 is still on
        hass = _make_hass({
            "binary_sensor.motion1": STATE_OFF,
            "binary_sensor.motion2": STATE_ON,
        })

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch(
            'custom_components.auto_areas.binary_sensors.presence.async_call_later'
        ) as mock_call_later:
            with patch.object(sensor, 'async_write_ha_state'):
                await sensor._handle_state_change(event)

        # No timeout started — motion2 still on
        mock_call_later.assert_not_called()
        assert sensor.presence is True

    @pytest.mark.asyncio
    async def test_timeout_starts_when_last_sensor_off(self):
        """Timeout starts when the last sensor goes off."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1", "binary_sensor.motion2"]
        # Both off now
        hass = _make_hass({
            "binary_sensor.motion1": STATE_OFF,
            "binary_sensor.motion2": STATE_OFF,
        })

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        event = _make_event("binary_sensor.motion2", STATE_ON, STATE_OFF)

        with patch(
            'custom_components.auto_areas.binary_sensors.presence.async_call_later'
        ) as mock_call_later:
            mock_call_later.return_value = MagicMock()
            with patch.object(sensor, 'async_write_ha_state'):
                await sensor._handle_state_change(event)

        mock_call_later.assert_called_once()
        assert sensor.presence is True


class TestRemovalCleanup:
    """Test that timeout task is cancelled on entity removal."""

    @pytest.mark.asyncio
    async def test_timeout_cancelled_on_removal(self):
        """Pending timeout should be cancelled when entity is removed."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass()

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)

        cancel_mock = MagicMock()
        sensor._timeout_cancel = cancel_mock

        with patch.object(
            type(sensor).__mro__[2], 'async_will_remove_from_hass',
            new_callable=AsyncMock,
        ):
            await sensor.async_will_remove_from_hass()

        cancel_mock.assert_called_once()
        assert sensor._timeout_cancel is None

    @pytest.mark.asyncio
    async def test_removal_without_pending_timeout(self):
        """Removal should work cleanly even with no pending timeout."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass()

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor._timeout_cancel = None

        with patch.object(
            type(sensor).__mro__[2], 'async_will_remove_from_hass',
            new_callable=AsyncMock,
        ):
            await sensor.async_will_remove_from_hass()

        assert sensor._timeout_cancel is None


class TestReentryDuringTimeout:
    """Test that re-entry during timeout keeps presence on."""

    @pytest.mark.asyncio
    async def test_presence_stays_on_throughout_reentry(self):
        """Presence stays True when sensor re-triggers during pending timeout."""
        auto_area = _make_auto_area(presence_timeout=30)
        entity_ids = ["binary_sensor.motion1"]
        hass = _make_hass({"binary_sensor.motion1": STATE_OFF})

        sensor = _create_presence_sensor(hass, auto_area, entity_ids)
        sensor.presence = True

        # Step 1: Sensor goes off → timeout starts
        off_event = _make_event("binary_sensor.motion1", STATE_ON, STATE_OFF)

        with patch(
            'custom_components.auto_areas.binary_sensors.presence.async_call_later'
        ) as mock_call_later:
            cancel_mock = MagicMock()
            mock_call_later.return_value = cancel_mock
            with patch.object(sensor, 'async_write_ha_state'):
                await sensor._handle_state_change(off_event)

        assert sensor.presence is True
        assert sensor._timeout_cancel is cancel_mock

        # Step 2: Sensor triggers again → timer cancelled, presence stays True
        on_event = _make_event("binary_sensor.motion1", STATE_OFF, STATE_ON)

        with patch.object(sensor, 'async_write_ha_state'):
            await sensor._handle_state_change(on_event)

        cancel_mock.assert_called_once()
        assert sensor._timeout_cancel is None
        assert sensor.presence is True
