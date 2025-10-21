"""Test Auto Lights functionality."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from homeassistant.const import STATE_ON, STATE_OFF

from custom_components.auto_areas.auto_lights import AutoLights
from custom_components.auto_areas.const import (
    CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
    CONFIG_IS_SLEEPING_AREA,
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
)


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def mock_auto_area(mock_hass):
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = "test_room"
    auto_area.hass = mock_hass
    auto_area.config_entry = MagicMock()
    auto_area.config_entry.options = {
        CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 100,
        CONFIG_IS_SLEEPING_AREA: False,
        CONFIG_EXCLUDED_LIGHT_ENTITIES: [],
    }
    return auto_area


@pytest.fixture
def auto_lights(mock_auto_area):
    """Create an AutoLights instance."""
    return AutoLights(mock_auto_area)


def create_state_change_event(entity_id, old_state_value, new_state_value):
    """Helper to create state change event."""
    old_state = MagicMock() if old_state_value is not None else None
    if old_state:
        old_state.state = old_state_value

    new_state = MagicMock() if new_state_value is not None else None
    if new_state:
        new_state.state = new_state_value

    event = MagicMock()
    event.data = {
        "entity_id": entity_id,
        "old_state": old_state,
        "new_state": new_state,
    }
    return event


class TestAutoLightsInitialization:
    """Test AutoLights initialization."""

    def test_init_with_default_config(self, auto_lights, mock_auto_area):
        """Test initialization with default configuration."""
        assert auto_lights.auto_area == mock_auto_area
        assert auto_lights.hass == mock_auto_area.hass
        assert auto_lights.illuminance_threshold == 100
        assert auto_lights.is_sleeping_area is False
        assert auto_lights.excluded_light_entities == []

    def test_init_sleeping_area(self, mock_auto_area):
        """Test initialization with sleeping area enabled."""
        mock_auto_area.config_entry.options[CONFIG_IS_SLEEPING_AREA] = True
        auto_lights = AutoLights(mock_auto_area)
        assert auto_lights.is_sleeping_area is True

    def test_entity_ids_constructed_correctly(self, auto_lights):
        """Test that entity IDs are constructed with correct prefixes."""
        assert "test_room" in auto_lights.presence_entity_id
        assert "test_room" in auto_lights.illuminance_entity_id
        assert "test_room" in auto_lights.light_group_entity_id


class TestIlluminanceHandling:
    """Test illuminance-related functionality."""

    def test_get_current_illuminance_success(self, auto_lights):
        """Test getting current illuminance successfully."""
        mock_state = MagicMock()
        mock_state.state = "50.5"
        auto_lights.hass.states.get.return_value = mock_state

        result = auto_lights.get_current_illuminance()

        assert result == 50.5

    def test_get_current_illuminance_none_state(self, auto_lights):
        """Test getting illuminance when entity doesn't exist."""
        auto_lights.hass.states.get.return_value = None

        result = auto_lights.get_current_illuminance()

        assert result is None

    def test_get_current_illuminance_invalid_value(self, auto_lights):
        """Test getting illuminance with invalid value."""
        mock_state = MagicMock()
        mock_state.state = "unavailable"
        auto_lights.hass.states.get.return_value = mock_state

        result = auto_lights.get_current_illuminance()

        assert result is None

    def test_is_below_illuminance_threshold_true(self, auto_lights):
        """Test illuminance check when below threshold."""
        mock_state = MagicMock()
        mock_state.state = "50"
        auto_lights.hass.states.get.return_value = mock_state

        result = auto_lights.is_below_illuminance_threshold()

        assert result is True

    def test_is_below_illuminance_threshold_false(self, auto_lights):
        """Test illuminance check when above threshold."""
        mock_state = MagicMock()
        mock_state.state = "150"
        auto_lights.hass.states.get.return_value = mock_state

        result = auto_lights.is_below_illuminance_threshold()

        assert result is False

    def test_is_below_illuminance_threshold_no_threshold(self, auto_lights):
        """Test illuminance check when threshold is 0."""
        auto_lights.illuminance_threshold = 0

        result = auto_lights.is_below_illuminance_threshold()

        assert result is True


class TestPresenceHandling:
    """Test presence detection and light control."""

    @pytest.mark.asyncio
    async def test_turn_lights_on(self, auto_lights):
        """Test turning lights on."""
        await auto_lights._turn_lights_on()

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is True

    @pytest.mark.asyncio
    async def test_turn_lights_off(self, auto_lights):
        """Test turning lights off."""
        await auto_lights._turn_lights_off()

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is False

    @pytest.mark.asyncio
    async def test_handle_presence_on_below_illuminance(self, auto_lights):
        """Test lights turn on when presence detected and dark."""
        auto_lights.sleep_mode_enabled = False
        mock_state = MagicMock()
        mock_state.state = "50"
        auto_lights.hass.states.get.return_value = mock_state

        event = create_state_change_event(
            auto_lights.presence_entity_id, STATE_OFF, STATE_ON
        )

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is True

    @pytest.mark.asyncio
    async def test_handle_presence_on_above_illuminance(self, auto_lights):
        """Test lights don't turn on when too bright."""
        auto_lights.sleep_mode_enabled = False
        mock_state = MagicMock()
        mock_state.state = "150"
        auto_lights.hass.states.get.return_value = mock_state

        event = create_state_change_event(
            auto_lights.presence_entity_id, STATE_OFF, STATE_ON
        )

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_presence_off(self, auto_lights):
        """Test lights turn off when presence cleared."""
        auto_lights.sleep_mode_enabled = False

        event = create_state_change_event(
            auto_lights.presence_entity_id, STATE_ON, STATE_OFF
        )

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is False


class TestSleepMode:
    """Test sleep mode functionality."""

    @pytest.mark.asyncio
    async def test_sleep_mode_prevents_lights_on(self, auto_lights):
        """Test that sleep mode prevents lights from turning on."""
        auto_lights.sleep_mode_enabled = True

        event = create_state_change_event(
            auto_lights.presence_entity_id, STATE_OFF, STATE_ON
        )

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_sleep_mode_enabled_turns_lights_off(self, auto_lights):
        """Test enabling sleep mode turns lights off."""
        event = create_state_change_event(
            auto_lights.sleep_mode_entity_id, STATE_OFF, STATE_ON
        )

        await auto_lights.handle_sleep_mode_state_change(event)

        assert auto_lights.sleep_mode_enabled is True
        auto_lights.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_sleep_mode_disabled_restores_lights(self, auto_lights):
        """Test disabling sleep mode turns lights on if presence detected."""
        auto_lights.sleep_mode_enabled = True
        mock_presence_state = MagicMock()
        mock_presence_state.state = STATE_ON

        mock_illuminance_state = MagicMock()
        mock_illuminance_state.state = "50"

        auto_lights.hass.states.get.side_effect = lambda entity_id: (
            mock_presence_state if "presence" in entity_id else mock_illuminance_state
        )

        event = create_state_change_event(
            auto_lights.sleep_mode_entity_id, STATE_ON, STATE_OFF
        )

        await auto_lights.handle_sleep_mode_state_change(event)

        assert auto_lights.sleep_mode_enabled is False
        auto_lights.hass.services.async_call.assert_called_once()


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_unsubscribes_listeners(self, auto_lights):
        """Test cleanup unsubscribes all event listeners."""
        auto_lights.unsubscribe_sleep_mode = MagicMock()
        auto_lights.unsubscribe_presence = MagicMock()
        auto_lights.unsubscribe_illuminance = MagicMock()

        auto_lights.cleanup()

        auto_lights.unsubscribe_sleep_mode.assert_called_once()
        auto_lights.unsubscribe_presence.assert_called_once()
        auto_lights.unsubscribe_illuminance.assert_called_once()

    def test_cleanup_with_none_listeners(self, auto_lights):
        """Test cleanup handles None listeners gracefully."""
        auto_lights.unsubscribe_sleep_mode = None
        auto_lights.unsubscribe_presence = None
        auto_lights.unsubscribe_illuminance = None

        auto_lights.cleanup()
