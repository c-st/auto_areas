"""Test switch entities."""
from unittest.mock import MagicMock
import pytest
from homeassistant.components.switch import SwitchDeviceClass

from custom_components.auto_areas.switches.sleep_mode import SleepModeSwitch
from custom_components.auto_areas.switches.presence_lock import PresenceLockSwitch


@pytest.fixture
def mock_auto_area():
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = "Test Room"
    auto_area.config_entry = MagicMock()
    auto_area.config_entry.entry_id = "test_entry_id"
    auto_area.device_info = {
        "identifiers": {("auto_areas", "test_entry_id")},
        "name": "Test Room Auto Areas",
    }
    return auto_area


class TestSleepModeSwitch:
    """Test SleepModeSwitch."""

    def test_initialization(self, mock_auto_area):
        """Test switch initialization."""
        switch = SleepModeSwitch(mock_auto_area)

        assert switch.auto_area == mock_auto_area
        assert switch._is_on is False
        assert switch._attr_should_poll is False

    def test_name(self, mock_auto_area):
        """Test switch name."""
        switch = SleepModeSwitch(mock_auto_area)

        name = switch.name
        assert "Test Room" in name
        assert "Sleep Mode" in name

    def test_unique_id(self, mock_auto_area):
        """Test unique ID generation."""
        switch = SleepModeSwitch(mock_auto_area)

        unique_id = switch.unique_id
        assert "test_entry_id" in unique_id
        assert "sleep_mode" in unique_id

    def test_device_info(self, mock_auto_area):
        """Test device info."""
        switch = SleepModeSwitch(mock_auto_area)

        device_info = switch.device_info
        assert device_info == mock_auto_area.device_info

    def test_device_class(self, mock_auto_area):
        """Test device class."""
        switch = SleepModeSwitch(mock_auto_area)

        assert switch.device_class == SwitchDeviceClass.SWITCH

    def test_is_on_default(self, mock_auto_area):
        """Test default is_on state."""
        switch = SleepModeSwitch(mock_auto_area)

        assert switch.is_on is False

    def test_turn_on(self, mock_auto_area):
        """Test turning switch on."""
        switch = SleepModeSwitch(mock_auto_area)
        switch.schedule_update_ha_state = MagicMock()

        switch.turn_on()

        assert switch._is_on is True
        assert switch.is_on is True
        switch.schedule_update_ha_state.assert_called_once()

    def test_turn_off(self, mock_auto_area):
        """Test turning switch off."""
        switch = SleepModeSwitch(mock_auto_area)
        switch._is_on = True
        switch.schedule_update_ha_state = MagicMock()

        switch.turn_off()

        assert switch._is_on is False
        assert switch.is_on is False
        switch.schedule_update_ha_state.assert_called_once()

    def test_turn_on_then_off(self, mock_auto_area):
        """Test turning switch on then off."""
        switch = SleepModeSwitch(mock_auto_area)
        switch.schedule_update_ha_state = MagicMock()

        switch.turn_on()
        assert switch.is_on is True

        switch.turn_off()
        assert switch.is_on is False

        assert switch.schedule_update_ha_state.call_count == 2


class TestPresenceLockSwitch:
    """Test PresenceLockSwitch."""

    def test_initialization(self, mock_auto_area):
        """Test switch initialization."""
        switch = PresenceLockSwitch(mock_auto_area)

        assert switch.auto_area == mock_auto_area
        assert switch._is_on is False
        assert switch._attr_should_poll is False

    def test_name(self, mock_auto_area):
        """Test switch name."""
        switch = PresenceLockSwitch(mock_auto_area)

        name = switch.name
        assert "Test Room" in name
        assert "Presence Lock" in name

    def test_unique_id(self, mock_auto_area):
        """Test unique ID generation."""
        switch = PresenceLockSwitch(mock_auto_area)

        unique_id = switch.unique_id
        assert "test_entry_id" in unique_id
        assert "presence_lock" in unique_id

    def test_device_info(self, mock_auto_area):
        """Test device info."""
        switch = PresenceLockSwitch(mock_auto_area)

        device_info = switch.device_info
        assert device_info == mock_auto_area.device_info

    def test_device_class(self, mock_auto_area):
        """Test device class."""
        switch = PresenceLockSwitch(mock_auto_area)

        assert switch.device_class == SwitchDeviceClass.SWITCH

    def test_is_on_default(self, mock_auto_area):
        """Test default is_on state."""
        switch = PresenceLockSwitch(mock_auto_area)

        assert switch.is_on is False

    def test_turn_on(self, mock_auto_area):
        """Test turning switch on."""
        switch = PresenceLockSwitch(mock_auto_area)
        switch.schedule_update_ha_state = MagicMock()

        switch.turn_on()

        assert switch._is_on is True
        assert switch.is_on is True
        switch.schedule_update_ha_state.assert_called_once()

    def test_turn_off(self, mock_auto_area):
        """Test turning switch off."""
        switch = PresenceLockSwitch(mock_auto_area)
        switch._is_on = True
        switch.schedule_update_ha_state = MagicMock()

        switch.turn_off()

        assert switch._is_on is False
        assert switch.is_on is False
        switch.schedule_update_ha_state.assert_called_once()

    def test_toggle_multiple_times(self, mock_auto_area):
        """Test toggling switch multiple times."""
        switch = PresenceLockSwitch(mock_auto_area)
        switch.schedule_update_ha_state = MagicMock()

        # Off -> On
        switch.turn_on()
        assert switch.is_on is True

        # On -> Off
        switch.turn_off()
        assert switch.is_on is False

        # Off -> On
        switch.turn_on()
        assert switch.is_on is True

        assert switch.schedule_update_ha_state.call_count == 3
