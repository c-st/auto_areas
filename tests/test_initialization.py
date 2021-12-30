"""Tests for verifying component setup"""
import logging

from homeassistant.helpers import device_registry as dev_reg
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import DATA_AUTO_AREA, DOMAIN
from custom_components.auto_areas.ha_helpers import get_data
from tests.conftest import create_entity

_LOGGER = logging.getLogger(__name__)


async def test_area_initialization(hass, default_entities):
    """Verify area initialization"""

    # setup component
    config: dict = {"auto_areas": {"bedroom": {"is_sleeping_area": False}}}
    result = await async_setup_component(hass, DOMAIN, config)
    assert result is True

    # verify that areas have been registered
    auto_areas: dict[str, AutoArea] = get_data(hass, DATA_AUTO_AREA)
    assert len(auto_areas) is 4

    # verify entities amount
    assert len(auto_areas["kitchen"].entities) is 0
    assert len(auto_areas["living_room"].entities) is 2
    assert len(auto_areas["bedroom"].entities) is 1
    assert len(auto_areas["bathroom"].entities) is 1


async def test_area_assignment_through_device(
    hass, device_registry, entity_registry, default_areas
):
    """Verify that entities assigned to an area through their device are recognized"""

    # Create device
    bedroom_area_id = default_areas["bedroom"].id
    config_entry = MockConfigEntry(domain="light")
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dev_reg.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        entry_type=dev_reg.DeviceEntryType.SERVICE,
        sw_version="sw-version",
        name="name",
        manufacturer="manufacturer",
        model="model",
    )
    # Assign to area bedroom
    device_registry.async_update_device(device.id, area_id=bedroom_area_id)
    create_entity(
        entity_registry, "light", "bathroom2", area_id=None, device_id=device.id
    )

    # Setup component
    result = await async_setup_component(hass, DOMAIN, {})
    assert result is True

    auto_areas: dict[str, AutoArea] = get_data(hass, DATA_AUTO_AREA)
    assert len(auto_areas["kitchen"].entities) is 0
    assert len(auto_areas["living_room"].entities) is 0
    assert len(auto_areas["bedroom"].entities) is 1
    assert len(auto_areas["bathroom"].entities) is 0


async def test_entity_domain_filtering(hass, entity_registry, default_entities):
    """Verify only entities from supported domains are registered"""
    create_entity(entity_registry, domain="foo", area_id="bedroom")
    create_entity(entity_registry, domain="bar", area_id="bathroom")

    result = await async_setup_component(hass, DOMAIN, {})
    assert result is True

    auto_areas: dict[str, AutoArea] = get_data(hass, DATA_AUTO_AREA)
    assert len(auto_areas["bedroom"].entities) is 1
    assert len(auto_areas["bathroom"].entities) is 1
