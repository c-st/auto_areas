"""Test Presence Binary Sensor functionality."""
from unittest.mock import MagicMock, patch
import pytest
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant, Event
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.auto_areas.binary_sensors.presence import PresenceBinarySensor
from custom_components.auto_areas.const import PRESENCE_ON_STATES


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_auto_area():
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = "test_room"
    auto_area.slugified_area_name = "test_room"
    auto_area.config_entry = MagicMock()
    auto_area.config_entry.entry_id = "test_entry_id"
    return auto_area


@pytest.fixture
def mock_entities():
    """Create mock entity entries."""
    motion_sensor = MagicMock()
    motion_sensor.entity_id = "binary_sensor.test_motion"
    motion_sensor.device_class = BinarySensorDeviceClass.MOTION
    motion_sensor.original_device_class = BinarySensorDeviceClass.MOTION
    motion_sensor.platform = "mqtt"

    occupancy_sensor = MagicMock()
    occupancy_sensor.entity_id = "binary_sensor.test_occupancy"
    occupancy_sensor.device_class = BinarySensorDeviceClass.OCCUPANCY
    occupancy_sensor.original_device_class = BinarySensorDeviceClass.OCCUPANCY
    occupancy_sensor.platform = "zha"

    return [motion_sensor, occupancy_sensor]


@pytest.fixture
def presence_sensor(mock_hass, mock_auto_area, mock_entities):
    """Create a PresenceBinarySensor instance."""
    mock_auto_area.get_valid_entities.return_value = mock_entities
    return PresenceBinarySensor(mock_hass, mock_auto_area)


class TestPresenceSensorInitialization:
    """Test PresenceBinarySensor initialization."""

    def test_init_creates_sensor(self, presence_sensor, mock_auto_area):
        """Test initialization creates sensor correctly."""
        assert presence_sensor.auto_area == mock_auto_area
        assert presence_sensor.presence is None

    def test_unique_id_generated(self, presence_sensor):
        """Test unique ID is generated from entry ID."""
        unique_id = presence_sensor.unique_id
        assert "test_entry_id" in unique_id
        assert "aggregated_presence" in unique_id

    def test_get_sensor_entities(self, presence_sensor, mock_entities):
        """Test sensor entity collection."""
        entity_ids = presence_sensor._get_sensor_entities()

        # Should include presence lock switch and both mock sensors
        assert len(entity_ids) >= 3
        assert any("presence_lock" in eid for eid in entity_ids)
        assert "binary_sensor.test_motion" in entity_ids
        assert "binary_sensor.test_occupancy" in entity_ids

    def test_excludes_auto_areas_entities(self, mock_hass, mock_auto_area):
        """Test that entities from auto_areas domain are excluded."""
        auto_area_entity = MagicMock()
        auto_area_entity.entity_id = "binary_sensor.auto_areas_presence"
        auto_area_entity.device_class = BinarySensorDeviceClass.OCCUPANCY
        auto_area_entity.original_device_class = BinarySensorDeviceClass.OCCUPANCY
        auto_area_entity.platform = "auto_areas"

        other_entity = MagicMock()
        other_entity.entity_id = "binary_sensor.other_motion"
        other_entity.device_class = BinarySensorDeviceClass.MOTION
        other_entity.original_device_class = BinarySensorDeviceClass.MOTION
        other_entity.platform = "mqtt"

        mock_auto_area.get_valid_entities.return_value = [auto_area_entity, other_entity]

        sensor = PresenceBinarySensor(mock_hass, mock_auto_area)
        entity_ids = sensor._get_sensor_entities()

        # Should exclude auto_areas entity
        assert "binary_sensor.auto_areas_presence" not in entity_ids
        assert "binary_sensor.other_motion" in entity_ids


class TestPresenceState:
    """Test presence state management."""

    def test_state_none_initially(self, presence_sensor):
        """Test state is None before initialization."""
        presence_sensor.presence = None
        assert presence_sensor.state is None

    def test_state_on_when_presence_detected(self, presence_sensor):
        """Test state is 'on' when presence is detected."""
        presence_sensor.presence = True
        assert presence_sensor.state == STATE_ON

    def test_state_off_when_no_presence(self, presence_sensor):
        """Test state is 'off' when no presence."""
        presence_sensor.presence = False
        assert presence_sensor.state == STATE_OFF


class TestPresenceDetection:
    """Test presence detection logic."""

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.binary_sensors.presence.all_states_are_off")
    @patch("custom_components.auto_areas.binary_sensors.presence.async_track_state_change_event")
    async def test_initial_presence_detected(
        self, mock_track, mock_all_off, presence_sensor
    ):
        """Test initial presence detection when sensor is on."""
        mock_all_off.return_value = False  # At least one sensor is on
        presence_sensor.schedule_update_ha_state = MagicMock()

        await presence_sensor.async_added_to_hass()

        assert presence_sensor.presence is True
        presence_sensor.schedule_update_ha_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.binary_sensors.presence.all_states_are_off")
    @patch("custom_components.auto_areas.binary_sensors.presence.async_track_state_change_event")
    async def test_initial_no_presence(
        self, mock_track, mock_all_off, presence_sensor
    ):
        """Test initial state when no presence detected."""
        mock_all_off.return_value = True  # All sensors are off
        presence_sensor.schedule_update_ha_state = MagicMock()

        await presence_sensor.async_added_to_hass()

        assert presence_sensor.presence is False
        presence_sensor.schedule_update_ha_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.binary_sensors.presence.async_track_state_change_event")
    async def test_subscribes_to_state_changes(
        self, mock_track, presence_sensor
    ):
        """Test that sensor subscribes to state changes."""
        presence_sensor.schedule_update_ha_state = MagicMock()

        with patch("custom_components.auto_areas.binary_sensors.presence.all_states_are_off"):
            await presence_sensor.async_added_to_hass()

        mock_track.assert_called_once()


class TestStateChangeHandling:
    """Test state change event handling."""

    @pytest.mark.asyncio
    async def test_presence_detected_on_sensor_on(self, presence_sensor):
        """Test presence is detected when sensor turns on."""
        presence_sensor.presence = False
        presence_sensor.schedule_update_ha_state = MagicMock()

        # Create event
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        assert presence_sensor.presence is True
        presence_sensor.schedule_update_ha_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.binary_sensors.presence.all_states_are_off")
    async def test_presence_cleared_when_all_sensors_off(
        self, mock_all_off, presence_sensor
    ):
        """Test presence is cleared when all sensors turn off."""
        presence_sensor.presence = True
        presence_sensor.schedule_update_ha_state = MagicMock()
        mock_all_off.return_value = True  # All sensors are off

        # Create event
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_OFF),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        assert presence_sensor.presence is False
        presence_sensor.schedule_update_ha_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.binary_sensors.presence.all_states_are_off")
    async def test_presence_maintained_when_other_sensor_on(
        self, mock_all_off, presence_sensor
    ):
        """Test presence is maintained when other sensors are still on."""
        presence_sensor.presence = True
        presence_sensor.schedule_update_ha_state = MagicMock()
        mock_all_off.return_value = False  # Other sensors still on

        # Create event
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_OFF),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        # Presence should still be True
        assert presence_sensor.presence is True
        # State should not be updated
        presence_sensor.schedule_update_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_update_on_same_state(self, presence_sensor):
        """Test no update when state doesn't change."""
        presence_sensor.presence = True
        presence_sensor.schedule_update_ha_state = MagicMock()

        # Create event with same state
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        # Should return early without update
        presence_sensor.schedule_update_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_duplicate_presence_on(self, presence_sensor):
        """Test no duplicate updates when presence already detected."""
        presence_sensor.presence = True
        presence_sensor.schedule_update_ha_state = MagicMock()

        # Create event
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        # Should not update again since presence was already True
        presence_sensor.schedule_update_ha_state.assert_not_called()

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.binary_sensors.presence.all_states_are_off")
    async def test_no_duplicate_presence_off(
        self, mock_all_off, presence_sensor
    ):
        """Test no duplicate updates when presence already cleared."""
        presence_sensor.presence = False
        presence_sensor.schedule_update_ha_state = MagicMock()
        mock_all_off.return_value = True

        # Create event
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_OFF),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        # Should not update again since presence was already False
        presence_sensor.schedule_update_ha_state.assert_not_called()


class TestPresenceOnStates:
    """Test different presence on states."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("on_state", PRESENCE_ON_STATES)
    async def test_all_presence_on_states_detected(self, presence_sensor, on_state):
        """Test that all configured ON states trigger presence detection."""
        presence_sensor.presence = False
        presence_sensor.schedule_update_ha_state = MagicMock()

        # Create event
        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=on_state),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await presence_sensor._handle_state_change(event)

        assert presence_sensor.presence is True
        presence_sensor.schedule_update_ha_state.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_handle_none_from_state(self, presence_sensor):
        """Test handling event with None old_state."""
        presence_sensor.presence = False
        presence_sensor.schedule_update_ha_state = MagicMock()

        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": None,
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        # Should handle gracefully
        await presence_sensor._handle_state_change(event)

        assert presence_sensor.presence is True

    @pytest.mark.asyncio
    async def test_handle_none_to_state(self, presence_sensor):
        """Test handling event with None new_state."""
        presence_sensor.presence = True
        presence_sensor.schedule_update_ha_state = MagicMock()

        event_data = {
            "entity_id": "binary_sensor.test_motion",
            "old_state": MagicMock(state=STATE_ON),
            "new_state": None,
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        # Should handle gracefully and not crash
        await presence_sensor._handle_state_change(event)

    def test_entity_collection_with_no_entities(self, mock_hass, mock_auto_area):
        """Test sensor handles areas with no presence entities."""
        mock_auto_area.get_valid_entities.return_value = []

        sensor = PresenceBinarySensor(mock_hass, mock_auto_area)
        entity_ids = sensor._get_sensor_entities()

        # Should at least have the presence lock switch
        assert len(entity_ids) >= 1
        assert any("presence_lock" in eid for eid in entity_ids)
