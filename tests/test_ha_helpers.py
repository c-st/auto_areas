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


def _registries(hass):
    """Return the real (area, entity, device) registries."""
    from homeassistant.helpers import area_registry as ar
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    return ar.async_get(hass), er.async_get(hass), dr.async_get(hass)


def _add_entity(entity_registry, domain, unique_id, area_id=None, device_id=None):
    """Register an entity, optionally pinned to an area or a device."""
    entry = entity_registry.async_get_or_create(
        domain=domain, platform="test", unique_id=unique_id, device_id=device_id
    )
    if area_id is not None:
        entry = entity_registry.async_update_entity(entry.entity_id, area_id=area_id)
    return entry


def _add_device(hass, device_registry, identifier, area_id=None):
    """Register a device, optionally assigned to an area."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("test", identifier)},
    )
    if area_id is not None:
        device = device_registry.async_update_device(device.id, area_id=area_id)
    return device


class TestGetAllEntities:
    """Test get_all_entities against real Home Assistant registries."""

    async def test_domain_filter(self, hass):
        """Only entities in the requested domains are returned."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        area = area_registry.async_create("Living Room")

        temp = _add_entity(entity_registry, "sensor", "temp", area_id=area.id)
        lamp = _add_entity(entity_registry, "light", "lamp", area_id=area.id)
        humidity = _add_entity(entity_registry, "sensor", "humidity", area_id=area.id)

        result = get_all_entities(
            entity_registry, device_registry, area.id, domains=["sensor"]
        )

        entity_ids = [e.entity_id for e in result]
        assert temp.entity_id in entity_ids
        assert humidity.entity_id in entity_ids
        assert lamp.entity_id not in entity_ids

    async def test_no_domain_filter_returns_none(self, hass):
        """domains=None matches nothing (preserved original behaviour)."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        area = area_registry.async_create("Living Room")
        _add_entity(entity_registry, "sensor", "temp", area_id=area.id)

        result = get_all_entities(
            entity_registry, device_registry, area.id, domains=None
        )

        assert result == []

    async def test_filters_by_entity_area_id(self, hass):
        """Entities from other areas are excluded."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        living_room = area_registry.async_create("Living Room")
        bedroom = area_registry.async_create("Bedroom")

        temp = _add_entity(entity_registry, "sensor", "temp", area_id=living_room.id)
        _add_entity(entity_registry, "sensor", "temp2", area_id=bedroom.id)

        result = get_all_entities(
            entity_registry, device_registry, living_room.id, domains=["sensor"]
        )

        assert [e.entity_id for e in result] == [temp.entity_id]

    async def test_falls_back_to_device_area_id(self, hass):
        """An entity with no area of its own inherits its device's area."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        area = area_registry.async_create("Living Room")

        device = _add_device(hass, device_registry, "dev1", area_id=area.id)
        temp = _add_entity(entity_registry, "sensor", "temp", device_id=device.id)

        result = get_all_entities(
            entity_registry, device_registry, area.id, domains=["sensor"]
        )

        assert [e.entity_id for e in result] == [temp.entity_id]

    async def test_entity_area_overrides_device_area(self, hass):
        """An entity's own area wins over the area of its device."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        living_room = area_registry.async_create("Living Room")
        bedroom = area_registry.async_create("Bedroom")

        device = _add_device(hass, device_registry, "dev1", area_id=living_room.id)
        moved = _add_entity(
            entity_registry, "sensor", "temp", area_id=bedroom.id, device_id=device.id
        )

        # The device sits in the living room, but the entity was moved out of it.
        living_room_result = get_all_entities(
            entity_registry, device_registry, living_room.id, domains=["sensor"]
        )
        assert living_room_result == []

        bedroom_result = get_all_entities(
            entity_registry, device_registry, bedroom.id, domains=["sensor"]
        )
        assert [e.entity_id for e in bedroom_result] == [moved.entity_id]

    async def test_no_duplicates_when_entity_and_device_share_area(self, hass):
        """An entity in the same area as its device is returned exactly once."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        area = area_registry.async_create("Living Room")

        device = _add_device(hass, device_registry, "dev1", area_id=area.id)
        temp = _add_entity(
            entity_registry, "sensor", "temp", area_id=area.id, device_id=device.id
        )

        result = get_all_entities(
            entity_registry, device_registry, area.id, domains=["sensor"]
        )

        assert [e.entity_id for e in result] == [temp.entity_id]

    async def test_excludes_entities_from_other_areas(self, hass):
        """An area with no matching entities returns nothing."""
        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry, entity_registry, device_registry = _registries(hass)
        living_room = area_registry.async_create("Living Room")
        kitchen = area_registry.async_create("Kitchen")
        _add_entity(entity_registry, "sensor", "temp", area_id=kitchen.id)

        result = get_all_entities(
            entity_registry, device_registry, living_room.id, domains=["sensor"]
        )

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


class TestGetAllEntitiesScaling:
    """Cost of get_all_entities must scale with the area, not the whole registry.

    Regression guard for the HA 2026.9 startup stall: get_all_entities() used to
    walk every entity in the registry (~4,768 on a large install) and resolve a
    device for each one, and it is called once per auto entity per area. That
    blocked the event loop for ~13-15s per sensor, so HA never became reachable.
    """

    async def test_does_not_iterate_whole_registry(self, hass, monkeypatch):
        """It must use the registry's indexed area lookups, never a full scan."""
        from homeassistant.helpers import area_registry as ar
        from homeassistant.helpers import device_registry as dr
        from homeassistant.helpers import entity_registry as er
        from homeassistant.helpers.entity_registry import EntityRegistryItems

        from custom_components.auto_areas.ha_helpers import get_all_entities

        area_registry = ar.async_get(hass)
        entity_registry = er.async_get(hass)
        device_registry = dr.async_get(hass)

        target = area_registry.async_create("Target Room")
        other = area_registry.async_create("Other Room")

        wanted = entity_registry.async_get_or_create(
            domain="sensor", platform="test", unique_id="wanted"
        )
        entity_registry.async_update_entity(wanted.entity_id, area_id=target.id)

        # Bulk of the registry lives in an unrelated area.
        for i in range(200):
            entry = entity_registry.async_get_or_create(
                domain="sensor", platform="test", unique_id=f"noise_{i}"
            )
            entity_registry.async_update_entity(entry.entity_id, area_id=other.id)

        # Only .items() is patched: that is what a full scan uses, while HA's
        # own storage save uses .values(), which must keep working.
        def _boom(*args, **kwargs):
            raise AssertionError(
                "get_all_entities performed a full registry scan"
            )

        monkeypatch.setattr(EntityRegistryItems, "items", _boom)

        result = get_all_entities(
            entity_registry, device_registry, target.id, domains=["sensor"]
        )

        assert [e.entity_id for e in result] == [wanted.entity_id]
