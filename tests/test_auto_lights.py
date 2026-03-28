"""Tests for AutoLights behavior."""

import pytest
from unittest.mock import MagicMock, AsyncMock


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


def _make_auto_area(area_name="living_room", options=None):
    """Create a mock AutoArea for AutoLights."""
    auto_area = MagicMock()
    auto_area.area_name = area_name
    auto_area.config_entry.options = options or {}
    auto_area.hass = MagicMock()
    auto_area.hass.services.async_call = AsyncMock()

    states_map = {}

    def get_state(entity_id):
        return states_map.get(entity_id)

    auto_area.hass.states.get = MagicMock(side_effect=get_state)
    auto_area._states_map = states_map  # for test setup
    return auto_area


def _create_auto_lights(auto_area):
    """Create an AutoLights instance."""
    from custom_components.auto_areas.auto_lights import AutoLights
    return AutoLights(auto_area)


class TestAutoLightsPresence:
    """Test lights respond to presence changes."""

    @pytest.mark.asyncio
    async def test_lights_turn_on_when_presence_detected(self):
        """Test lights turn on when presence detected."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False

        event = _make_event(lights.presence_entity_id, STATE_OFF, STATE_ON)

        await lights.handle_presence_state_change(event)

        auto_area.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_on",
            {"entity_id": lights.light_group_entity_id},
        )
        assert lights.lights_turned_on is True

    @pytest.mark.asyncio
    async def test_lights_turn_off_when_presence_clears(self):
        """Test lights turn off when presence clears."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False
        lights.lights_turned_on = True

        event = _make_event(lights.presence_entity_id, STATE_ON, STATE_OFF)

        await lights.handle_presence_state_change(event)

        auto_area.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_off",
            {"entity_id": lights.light_group_entity_id},
        )
        assert lights.lights_turned_on is False

    @pytest.mark.asyncio
    async def test_lights_stay_off_when_illuminance_above_threshold(self):
        """Test lights stay off when illuminance above threshold."""
        from custom_components.auto_areas.const import CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE

        auto_area = _make_auto_area(options={CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 100})
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False

        # Set illuminance state above threshold
        illuminance_state = _make_state(lights.illuminance_entity_id, "200")
        auto_area._states_map[lights.illuminance_entity_id] = illuminance_state

        event = _make_event(lights.presence_entity_id, STATE_OFF, STATE_ON)

        await lights.handle_presence_state_change(event)

        auto_area.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_change_event_ignored(self):
        """Test no change event ignored."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)

        event = _make_event(lights.presence_entity_id, STATE_ON, STATE_ON)

        await lights.handle_presence_state_change(event)

        auto_area.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_none_new_state_ignored(self):
        """Test none new state ignored."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)

        event = _make_event(lights.presence_entity_id, STATE_ON, None)

        await lights.handle_presence_state_change(event)

        auto_area.hass.services.async_call.assert_not_called()


class TestAutoLightsManualOverride:
    """Test manual light override prevents illuminance from turning lights back on."""

    @pytest.mark.asyncio
    async def test_lights_stay_off_after_manual_off_on_illuminance_change(self):
        """Main bug: lights should not turn back on when illuminance changes after manual off."""
        from custom_components.auto_areas.const import CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE

        auto_area = _make_auto_area(options={CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 100})
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False
        lights.lights_turned_on = True

        # Set presence on
        auto_area._states_map[lights.presence_entity_id] = _make_state(
            lights.presence_entity_id, STATE_ON
        )

        # Simulate manual light off (light group changes from on to off while presence is on)
        light_off_event = _make_event(lights.light_group_entity_id, STATE_ON, STATE_OFF)
        await lights.handle_light_group_state_change(light_off_event)

        assert lights.manually_turned_off is True

        # Set illuminance below threshold
        auto_area._states_map[lights.illuminance_entity_id] = _make_state(
            lights.illuminance_entity_id, "50"
        )

        # Illuminance change arrives — should NOT turn lights on
        illuminance_event = _make_event(lights.illuminance_entity_id, "200", "50")
        await lights.handle_illuminance_change(illuminance_event)

        auto_area.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_lights_work_normally_after_presence_cycle(self):
        """After presence clears and returns, manual override should be reset."""
        from custom_components.auto_areas.const import CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE

        auto_area = _make_auto_area(options={CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 100})
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False
        lights.lights_turned_on = True

        # Set presence on and simulate manual off
        auto_area._states_map[lights.presence_entity_id] = _make_state(
            lights.presence_entity_id, STATE_ON
        )
        light_off_event = _make_event(lights.light_group_entity_id, STATE_ON, STATE_OFF)
        await lights.handle_light_group_state_change(light_off_event)
        assert lights.manually_turned_off is True

        # Presence clears — should reset manual override
        presence_off_event = _make_event(lights.presence_entity_id, STATE_ON, STATE_OFF)
        await lights.handle_presence_state_change(presence_off_event)
        assert lights.manually_turned_off is False

        # Reset mock for next assertion
        auto_area.hass.services.async_call.reset_mock()

        # Presence returns — lights should turn on normally
        auto_area._states_map[lights.illuminance_entity_id] = _make_state(
            lights.illuminance_entity_id, "50"
        )
        presence_on_event = _make_event(lights.presence_entity_id, STATE_OFF, STATE_ON)
        await lights.handle_presence_state_change(presence_on_event)

        auto_area.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_on",
            {"entity_id": lights.light_group_entity_id},
        )

    @pytest.mark.asyncio
    async def test_illuminance_turns_on_lights_without_manual_override(self):
        """Without manual override, illuminance below threshold should turn lights on."""
        from custom_components.auto_areas.const import CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE

        auto_area = _make_auto_area(options={CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 100})
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False
        lights.lights_turned_on = False
        lights.manually_turned_off = False

        # Presence on, illuminance below threshold
        auto_area._states_map[lights.presence_entity_id] = _make_state(
            lights.presence_entity_id, STATE_ON
        )
        auto_area._states_map[lights.illuminance_entity_id] = _make_state(
            lights.illuminance_entity_id, "50"
        )

        illuminance_event = _make_event(lights.illuminance_entity_id, "200", "50")
        await lights.handle_illuminance_change(illuminance_event)

        auto_area.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_on",
            {"entity_id": lights.light_group_entity_id},
        )

    @pytest.mark.asyncio
    async def test_auto_turn_off_does_not_set_manual_override(self):
        """When auto_areas turns off lights, it should not be detected as manual override."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)
        lights.sleep_mode_enabled = False
        lights.lights_turned_on = True

        auto_area._states_map[lights.presence_entity_id] = _make_state(
            lights.presence_entity_id, STATE_ON
        )

        # Simulate auto_areas turning off lights (via _turn_lights_off)
        await lights._turn_lights_off()

        assert lights.manually_turned_off is False

    @pytest.mark.asyncio
    async def test_manual_override_cleared_when_lights_turn_on(self):
        """If lights turn on (by anyone), manual override should be cleared."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)
        lights.manually_turned_off = True

        light_on_event = _make_event(lights.light_group_entity_id, STATE_OFF, STATE_ON)
        await lights.handle_light_group_state_change(light_on_event)

        assert lights.manually_turned_off is False


class TestAutoLightsCleanup:
    """Test cleanup unsubscribes all listeners."""

    def test_cleanup_unsubscribes_all(self):
        """Test cleanup unsubscribes all."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)

        unsub_presence = MagicMock()
        unsub_illuminance = MagicMock()
        unsub_sleep = MagicMock()
        unsub_lights = MagicMock()

        lights.unsubscribe_presence = unsub_presence
        lights.unsubscribe_illuminance = unsub_illuminance
        lights.unsubscribe_sleep_mode = unsub_sleep
        lights.unsubscribe_lights = unsub_lights

        lights.cleanup()

        unsub_presence.assert_called_once()
        unsub_illuminance.assert_called_once()
        unsub_sleep.assert_called_once()
        unsub_lights.assert_called_once()

    def test_cleanup_handles_none_subscriptions(self):
        """Test cleanup handles none subscriptions."""
        auto_area = _make_auto_area()
        lights = _create_auto_lights(auto_area)

        lights.unsubscribe_presence = None
        lights.unsubscribe_illuminance = None
        lights.unsubscribe_sleep_mode = None

        # Should not raise
        lights.cleanup()
