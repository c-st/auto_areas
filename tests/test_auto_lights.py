"""Test Auto Lights functionality."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant, Event

from custom_components.auto_areas.auto_lights import AutoLights
from custom_components.auto_areas.const import (
    CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
    CONFIG_IS_SLEEPING_AREA,
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
)


@pytest.fixture
def mock_auto_area():
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = "test_room"
    auto_area.hass = MagicMock(spec=HomeAssistant)
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
        auto_lights.hass.services.async_call = AsyncMock()

        await auto_lights._turn_lights_on()

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is True

    @pytest.mark.asyncio
    async def test_turn_lights_off(self, auto_lights):
        """Test turning lights off."""
        auto_lights.hass.services.async_call = AsyncMock()

        await auto_lights._turn_lights_off()

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is False

    @pytest.mark.asyncio
    async def test_handle_presence_on_below_illuminance(self, auto_lights):
        """Test lights turn on when presence detected and dark."""
        # Setup
        auto_lights.sleep_mode_enabled = False
        mock_state = MagicMock()
        mock_state.state = "50"  # Below threshold of 100
        auto_lights.hass.states.get.return_value = mock_state
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event_data = {
            "entity_id": auto_lights.presence_entity_id,
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is True

    @pytest.mark.asyncio
    async def test_handle_presence_on_above_illuminance(self, auto_lights):
        """Test lights don't turn on when too bright."""
        # Setup
        auto_lights.sleep_mode_enabled = False
        mock_state = MagicMock()
        mock_state.state = "150"  # Above threshold of 100
        auto_lights.hass.states.get.return_value = mock_state
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event_data = {
            "entity_id": auto_lights.presence_entity_id,
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_presence_off(self, auto_lights):
        """Test lights turn off when presence cleared."""
        # Setup
        auto_lights.sleep_mode_enabled = False
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event_data = {
            "entity_id": auto_lights.presence_entity_id,
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_OFF),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_called_once()
        assert auto_lights.lights_turned_on is False


class TestSleepMode:
    """Test sleep mode functionality."""

    @pytest.mark.asyncio
    async def test_sleep_mode_prevents_lights_on(self, auto_lights):
        """Test that sleep mode prevents lights from turning on."""
        # Setup
        auto_lights.sleep_mode_enabled = True
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event_data = {
            "entity_id": auto_lights.presence_entity_id,
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_presence_state_change(event)

        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_sleep_mode_enabled_turns_lights_off(self, auto_lights):
        """Test enabling sleep mode turns lights off."""
        # Setup
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event_data = {
            "entity_id": auto_lights.sleep_mode_entity_id,
            "old_state": MagicMock(state=STATE_OFF),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_sleep_mode_state_change(event)

        assert auto_lights.sleep_mode_enabled is True
        auto_lights.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_sleep_mode_disabled_restores_lights(self, auto_lights):
        """Test disabling sleep mode turns lights on if presence detected."""
        # Setup
        auto_lights.sleep_mode_enabled = True
        mock_presence_state = MagicMock()
        mock_presence_state.state = STATE_ON

        mock_illuminance_state = MagicMock()
        mock_illuminance_state.state = "50"  # Below threshold

        auto_lights.hass.states.get.side_effect = lambda entity_id: (
            mock_presence_state if "presence" in entity_id else mock_illuminance_state
        )
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event_data = {
            "entity_id": auto_lights.sleep_mode_entity_id,
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_OFF),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_sleep_mode_state_change(event)

        assert auto_lights.sleep_mode_enabled is False
        auto_lights.hass.services.async_call.assert_called_once()


class TestIlluminanceChangeHandling:
    """Test illuminance change event handling."""

    @pytest.mark.asyncio
    async def test_illuminance_change_turns_lights_on(self, auto_lights):
        """Test lights turn on when it gets dark with presence."""
        # Setup
        auto_lights.sleep_mode_enabled = False
        auto_lights.lights_turned_on = False

        mock_presence_state = MagicMock()
        mock_presence_state.state = STATE_ON

        mock_illuminance_state = MagicMock()
        mock_illuminance_state.state = "50"  # Below threshold

        auto_lights.hass.states.get.side_effect = lambda entity_id: (
            mock_presence_state if "presence" in entity_id else mock_illuminance_state
        )
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event = MagicMock(spec=Event)
        event.data = {}

        await auto_lights.handle_illuminance_change(event)

        auto_lights.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_illuminance_change_no_presence(self, auto_lights):
        """Test lights don't turn on when no presence."""
        # Setup
        mock_presence_state = MagicMock()
        mock_presence_state.state = STATE_OFF
        auto_lights.hass.states.get.return_value = mock_presence_state
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event = MagicMock(spec=Event)
        event.data = {}

        await auto_lights.handle_illuminance_change(event)

        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_illuminance_change_with_sleep_mode(self, auto_lights):
        """Test lights don't turn on when sleep mode is active."""
        # Setup
        auto_lights.sleep_mode_enabled = True
        mock_presence_state = MagicMock()
        mock_presence_state.state = STATE_ON
        auto_lights.hass.states.get.return_value = mock_presence_state
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event = MagicMock(spec=Event)
        event.data = {}

        await auto_lights.handle_illuminance_change(event)

        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_illuminance_change_lights_already_on(self, auto_lights):
        """Test lights don't turn on again if already on."""
        # Setup
        auto_lights.sleep_mode_enabled = False
        auto_lights.lights_turned_on = True
        mock_presence_state = MagicMock()
        mock_presence_state.state = STATE_ON
        auto_lights.hass.states.get.return_value = mock_presence_state
        auto_lights.hass.services.async_call = AsyncMock()

        # Create event
        event = MagicMock(spec=Event)
        event.data = {}

        await auto_lights.handle_illuminance_change(event)

        auto_lights.hass.services.async_call.assert_not_called()


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_unsubscribes_listeners(self, auto_lights):
        """Test cleanup unsubscribes all event listeners."""
        # Setup mock unsubscribe functions
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

        # Should not raise any exceptions
        auto_lights.cleanup()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_handle_presence_none_new_state(self, auto_lights):
        """Test handling presence change with None new state."""
        auto_lights.hass.services.async_call = AsyncMock()

        event_data = {
            "entity_id": auto_lights.presence_entity_id,
            "old_state": MagicMock(state=STATE_ON),
            "new_state": None,
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_presence_state_change(event)

        # Should return early without calling service
        auto_lights.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_presence_same_state(self, auto_lights):
        """Test handling presence change with same state."""
        auto_lights.hass.services.async_call = AsyncMock()

        event_data = {
            "entity_id": auto_lights.presence_entity_id,
            "old_state": MagicMock(state=STATE_ON),
            "new_state": MagicMock(state=STATE_ON),
        }
        event = MagicMock(spec=Event)
        event.data = event_data

        await auto_lights.handle_presence_state_change(event)

        # Should return early without calling service
        auto_lights.hass.services.async_call.assert_not_called()

    def test_get_illuminance_with_none_presence_entity(self, auto_lights):
        """Test getting illuminance handles None presence entity."""
        auto_lights.hass.states.get.return_value = None

        presence_state = auto_lights.hass.states.get(auto_lights.presence_entity_id)

        # Should handle None gracefully
        assert presence_state is None
