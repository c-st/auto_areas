"""Tests for ha_helpers utility functions."""

from unittest.mock import MagicMock


STATE_UNAVAILABLE = "unavailable"


def _make_entity(entity_id, domain, area_id=None, device_id=None, disabled=False):
    """Create a mock RegistryEntry."""
    entity = MagicMock()
    entity.entity_id = entity_id
    entity.domain = domain
    entity.area_id = area_id
    entity.device_id = device_id
    entity.disabled = disabled
    return entity


def _make_entity_registry(entities):
    """Create a mock EntityRegistry from a list of entities."""
    registry = MagicMock()
    registry.entities = {e.entity_id: e for e in entities}
    return registry


def _make_device_registry(devices=None):
    """Create a mock DeviceRegistry."""
    registry = MagicMock()
    devices = devices or {}
    registry.devices.get = MagicMock(side_effect=lambda did: devices.get(did))
    return registry


def _make_device(area_id=None):
    """Create a mock device."""
    device = MagicMock()
    device.area_id = area_id
    return device


def _make_hass(states_map=None):
    """Create a mock HomeAssistant."""
    hass = MagicMock()
    states_map = states_map or {}

    def get_state(entity_id):
        if entity_id in states_map:
            state = MagicMock()
            state.entity_id = entity_id
            state.state = states_map[entity_id]
            return state
        return None

    hass.states.get = MagicMock(side_effect=get_state)
    return hass


class TestGetAllEntities:
    """Test get_all_entities."""

    def test_domain_filter(self):
        """Test domain filter."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        entities = [
            _make_entity("sensor.temp", "sensor", area_id="living_room"),
            _make_entity("light.lamp", "light", area_id="living_room"),
            _make_entity("sensor.humidity", "sensor", area_id="living_room"),
        ]
        er = _make_entity_registry(entities)
        dr = _make_device_registry()

        result = get_all_entities(er, dr, "living_room", domains=["sensor"])
        entity_ids = [e.entity_id for e in result]
        assert "sensor.temp" in entity_ids
        assert "sensor.humidity" in entity_ids
        assert "light.lamp" not in entity_ids

    def test_no_domain_filter_returns_none(self):
        """Without domains filter, no entities match (domains=None means domain not in None → skip)."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        entities = [
            _make_entity("sensor.temp", "sensor", area_id="living_room"),
        ]
        er = _make_entity_registry(entities)
        dr = _make_device_registry()

        # domains=None means the condition `entity.domain not in domains` raises TypeError
        # Actually looking at the code: `if domains is None or entity.domain not in domains`
        # When domains is None, the `or` short-circuits to True, so it skips (continues).
        result = get_all_entities(er, dr, "living_room", domains=None)
        assert result == []

    def test_filters_by_entity_area_id(self):
        """Test filters by entity area id."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        entities = [
            _make_entity("sensor.temp", "sensor", area_id="living_room"),
            _make_entity("sensor.temp2", "sensor", area_id="bedroom"),
        ]
        er = _make_entity_registry(entities)
        dr = _make_device_registry()

        result = get_all_entities(er, dr, "living_room", domains=["sensor"])
        assert len(result) == 1
        assert result[0].entity_id == "sensor.temp"

    def test_falls_back_to_device_area_id(self):
        """Test falls back to device area id."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        device = _make_device(area_id="living_room")
        entities = [
            _make_entity("sensor.temp", "sensor", area_id=None, device_id="dev1"),
        ]
        er = _make_entity_registry(entities)
        dr = _make_device_registry({"dev1": device})

        result = get_all_entities(er, dr, "living_room", domains=["sensor"])
        assert len(result) == 1
        assert result[0].entity_id == "sensor.temp"

    def test_excludes_entities_from_other_areas(self):
        """Test excludes entities from other areas."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        entities = [
            _make_entity("sensor.temp", "sensor", area_id="kitchen"),
        ]
        er = _make_entity_registry(entities)
        dr = _make_device_registry()

        result = get_all_entities(er, dr, "living_room", domains=["sensor"])
        assert result == []


class TestIsValidEntity:
    """Test is_valid_entity."""

    def test_disabled_entity(self):
        """Test disabled entity."""
        from custom_components.auto_areas.ha_helpers import is_valid_entity

        hass = _make_hass()
        entity = _make_entity("sensor.temp", "sensor", disabled=True)
        assert is_valid_entity(hass, entity) is False

    def test_unavailable_entity(self):
        """Test unavailable entity."""
        from custom_components.auto_areas.ha_helpers import is_valid_entity

        hass = _make_hass({"sensor.temp": STATE_UNAVAILABLE})
        entity = _make_entity("sensor.temp", "sensor", disabled=False)
        assert is_valid_entity(hass, entity) is False

    def test_valid_entity(self):
        """Test valid entity."""
        from custom_components.auto_areas.ha_helpers import is_valid_entity

        hass = _make_hass({"sensor.temp": "21.5"})
        entity = _make_entity("sensor.temp", "sensor", disabled=False)
        assert is_valid_entity(hass, entity) is True

    def test_entity_with_no_state(self):
        """Entity with no state object (not yet loaded) should be valid."""
        from custom_components.auto_areas.ha_helpers import is_valid_entity

        hass = _make_hass()  # states.get returns None
        entity = _make_entity("sensor.temp", "sensor", disabled=False)
        assert is_valid_entity(hass, entity) is True
