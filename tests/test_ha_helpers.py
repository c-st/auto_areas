"""Test Home Assistant helper functions."""
from unittest.mock import MagicMock
import pytest
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNAVAILABLE

from custom_components.auto_areas.ha_helpers import (
    get_all_entities,
    get_area_id,
    all_states_are_off,
    is_valid_entity,
)


@pytest.fixture
def mock_entity_registry():
    """Create a mock entity registry."""
    registry = MagicMock()
    registry.entities = {}
    return registry


@pytest.fixture
def mock_device_registry():
    """Create a mock device registry."""
    registry = MagicMock()
    registry.devices = {}
    return registry


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    return MagicMock()


def create_entity(entity_id, domain, area_id=None, device_id=None, disabled=False):
    """Create a mock registry entry."""
    entity = MagicMock()
    entity.entity_id = entity_id
    entity.domain = domain
    entity.area_id = area_id
    entity.device_id = device_id
    entity.disabled = disabled
    return entity


def create_device(device_id, area_id):
    """Create a mock device entry."""
    device = MagicMock()
    device.id = device_id
    device.area_id = area_id
    return device


class TestGetAllEntities:
    """Test get_all_entities function."""

    def test_get_entities_in_area(self, mock_entity_registry, mock_device_registry):
        """Test getting all entities in an area."""
        # Setup entities
        entity1 = create_entity("light.room1", "light", area_id="room1")
        entity2 = create_entity("light.room2", "light", area_id="room2")
        entity3 = create_entity("switch.room1", "switch", area_id="room1")

        mock_entity_registry.entities = {
            "light.room1": entity1,
            "light.room2": entity2,
            "switch.room1": entity3,
        }

        # Get entities for room1
        result = get_all_entities(
            mock_entity_registry, mock_device_registry, "room1"
        )

        assert len(result) == 2
        assert entity1 in result
        assert entity3 in result
        assert entity2 not in result

    def test_get_entities_with_domain_filter(
        self, mock_entity_registry, mock_device_registry
    ):
        """Test getting entities with domain filter."""
        entity1 = create_entity("light.room1", "light", area_id="room1")
        entity2 = create_entity("switch.room1", "switch", area_id="room1")

        mock_entity_registry.entities = {
            "light.room1": entity1,
            "switch.room1": entity2,
        }

        # Get only light entities
        result = get_all_entities(
            mock_entity_registry, mock_device_registry, "room1", domains=["light"]
        )

        assert len(result) == 1
        assert entity1 in result
        assert entity2 not in result

    def test_get_entities_with_device_area(
        self, mock_entity_registry, mock_device_registry
    ):
        """Test getting entities that inherit area from device."""
        # Entity without area, but device has area
        entity = create_entity("light.room1", "light", device_id="device1")
        device = create_device("device1", "room1")

        mock_entity_registry.entities = {"light.room1": entity}
        mock_device_registry.devices = {"device1": device}

        result = get_all_entities(
            mock_entity_registry, mock_device_registry, "room1"
        )

        assert len(result) == 1
        assert entity in result

    def test_get_entities_empty_area(
        self, mock_entity_registry, mock_device_registry
    ):
        """Test getting entities from empty area."""
        entity = create_entity("light.room1", "light", area_id="room1")
        mock_entity_registry.entities = {"light.room1": entity}

        result = get_all_entities(
            mock_entity_registry, mock_device_registry, "room2"
        )

        assert len(result) == 0

    def test_get_entities_multiple_domains(
        self, mock_entity_registry, mock_device_registry
    ):
        """Test getting entities with multiple domain filters."""
        entity1 = create_entity("light.room1", "light", area_id="room1")
        entity2 = create_entity("switch.room1", "switch", area_id="room1")
        entity3 = create_entity("sensor.room1", "sensor", area_id="room1")

        mock_entity_registry.entities = {
            "light.room1": entity1,
            "switch.room1": entity2,
            "sensor.room1": entity3,
        }

        result = get_all_entities(
            mock_entity_registry,
            mock_device_registry,
            "room1",
            domains=["light", "switch"],
        )

        assert len(result) == 2
        assert entity1 in result
        assert entity2 in result
        assert entity3 not in result


class TestGetAreaId:
    """Test get_area_id function."""

    def test_area_id_from_entity(self, mock_device_registry):
        """Test getting area_id directly from entity."""
        entity = create_entity("light.test", "light", area_id="room1")

        result = get_area_id(entity, mock_device_registry)

        assert result == "room1"

    def test_area_id_from_device(self, mock_device_registry):
        """Test getting area_id from device."""
        entity = create_entity("light.test", "light", device_id="device1")
        device = create_device("device1", "room1")

        mock_device_registry.devices = {"device1": device}

        result = get_area_id(entity, mock_device_registry)

        assert result == "room1"

    def test_area_id_no_area(self, mock_device_registry):
        """Test getting area_id when no area is assigned."""
        entity = create_entity("light.test", "light")

        result = get_area_id(entity, mock_device_registry)

        assert result is None

    def test_area_id_device_no_area(self, mock_device_registry):
        """Test getting area_id when device has no area."""
        entity = create_entity("light.test", "light", device_id="device1")
        device = create_device("device1", None)

        mock_device_registry.devices = {"device1": device}

        result = get_area_id(entity, mock_device_registry)

        assert result is None

    def test_area_id_device_not_found(self, mock_device_registry):
        """Test getting area_id when device is not found."""
        entity = create_entity("light.test", "light", device_id="device1")
        mock_device_registry.devices = {}

        result = get_area_id(entity, mock_device_registry)

        assert result is None

    def test_area_id_entity_overrides_device(self, mock_device_registry):
        """Test that entity area_id overrides device area_id."""
        entity = create_entity(
            "light.test", "light", area_id="room1", device_id="device1"
        )
        device = create_device("device1", "room2")

        mock_device_registry.devices = {"device1": device}

        result = get_area_id(entity, mock_device_registry)

        # Entity area should take precedence
        assert result == "room1"


class TestAllStatesAreOff:
    """Test all_states_are_off function."""

    def test_all_states_off(self, mock_hass):
        """Test when all states are off."""
        state1 = MagicMock()
        state1.state = STATE_OFF
        state2 = MagicMock()
        state2.state = STATE_OFF

        mock_hass.states.get.side_effect = lambda eid: (
            state1 if eid == "binary_sensor.motion1" else state2
        )

        result = all_states_are_off(
            mock_hass,
            ["binary_sensor.motion1", "binary_sensor.motion2"],
            [STATE_ON, "detected"],
        )

        assert result is True

    def test_one_state_on(self, mock_hass):
        """Test when one state is on."""
        state1 = MagicMock()
        state1.state = STATE_ON
        state2 = MagicMock()
        state2.state = STATE_OFF

        mock_hass.states.get.side_effect = lambda eid: (
            state1 if eid == "binary_sensor.motion1" else state2
        )

        result = all_states_are_off(
            mock_hass,
            ["binary_sensor.motion1", "binary_sensor.motion2"],
            [STATE_ON],
        )

        assert result is False

    def test_custom_on_state(self, mock_hass):
        """Test with custom on states."""
        state = MagicMock()
        state.state = "detected"

        mock_hass.states.get.return_value = state

        result = all_states_are_off(
            mock_hass, ["binary_sensor.motion1"], [STATE_ON, "detected"]
        )

        assert result is False

    def test_empty_entity_list(self, mock_hass):
        """Test with empty entity list."""
        result = all_states_are_off(mock_hass, [], [STATE_ON])

        assert result is True

    def test_none_state(self, mock_hass):
        """Test when state is None."""
        mock_hass.states.get.return_value = None

        result = all_states_are_off(
            mock_hass, ["binary_sensor.motion1"], [STATE_ON]
        )

        # None states are filtered out
        assert result is True

    def test_mixed_none_and_off(self, mock_hass):
        """Test with mix of None and off states."""
        state_off = MagicMock()
        state_off.state = STATE_OFF

        mock_hass.states.get.side_effect = lambda eid: (
            None if eid == "binary_sensor.motion1" else state_off
        )

        result = all_states_are_off(
            mock_hass,
            ["binary_sensor.motion1", "binary_sensor.motion2"],
            [STATE_ON],
        )

        assert result is True

    def test_unavailable_state_counts_as_off(self, mock_hass):
        """Test that unavailable states count as off."""
        state = MagicMock()
        state.state = STATE_UNAVAILABLE

        mock_hass.states.get.return_value = state

        result = all_states_are_off(
            mock_hass, ["binary_sensor.motion1"], [STATE_ON]
        )

        assert result is True


class TestIsValidEntity:
    """Test is_valid_entity function."""

    def test_valid_entity(self, mock_hass):
        """Test with valid entity."""
        entity = create_entity("light.test", "light", disabled=False)

        state = MagicMock()
        state.state = STATE_ON
        mock_hass.states.get.return_value = state

        result = is_valid_entity(mock_hass, entity)

        assert result is True

    def test_disabled_entity(self, mock_hass):
        """Test with disabled entity."""
        entity = create_entity("light.test", "light", disabled=True)

        result = is_valid_entity(mock_hass, entity)

        assert result is False

    def test_unavailable_entity(self, mock_hass):
        """Test with unavailable entity."""
        entity = create_entity("light.test", "light", disabled=False)

        state = MagicMock()
        state.state = STATE_UNAVAILABLE
        mock_hass.states.get.return_value = state

        result = is_valid_entity(mock_hass, entity)

        assert result is False

    def test_entity_no_state(self, mock_hass):
        """Test with entity that has no state."""
        entity = create_entity("light.test", "light", disabled=False)
        mock_hass.states.get.return_value = None

        result = is_valid_entity(mock_hass, entity)

        assert result is True

    def test_entity_off_state(self, mock_hass):
        """Test with entity in off state."""
        entity = create_entity("light.test", "light", disabled=False)

        state = MagicMock()
        state.state = STATE_OFF
        mock_hass.states.get.return_value = state

        result = is_valid_entity(mock_hass, entity)

        assert result is True
