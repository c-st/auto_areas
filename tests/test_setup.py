"""Tests for verifying component setup"""
import logging
from collections import OrderedDict
from typing import List

import pytest

from homeassistant.setup import async_setup_component
from homeassistant.helpers import (
    device_registry as dev_reg,
    entity_registry as ent_reg,
)

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)
from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import DOMAIN
from tests.conftest import create_entity

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="entities")
def fixture_entity_registry(areas, entity_registry) -> List[ent_reg.RegistryEntry]:
    """Entities assigned to areas"""
    return [
        create_entity(entity_registry, "light", unique_id="1", area_id="living_room"),
        create_entity(entity_registry, "light", unique_id="2", area_id="living_room"),
        create_entity(entity_registry, "light", unique_id="1", area_id="bedroom"),
        create_entity(entity_registry, "light", unique_id="1", area_id="bathroom"),
    ]


@pytest.fixture(name="devices")
async def fixture_devices(
    areas,
    device_registry: dev_reg.DeviceRegistry,
    entity_registry: ent_reg.EntityRegistry,
) -> None:
    """Entity which is assigned to an area via a device"""
    bedroom_area_id = areas["bedroom"].id
    config_entry = MockConfigEntry(domain="light")

    # Create device
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
    device_registry.async_update_device(device.id, area_id=bedroom_area_id)
    create_entity(
        entity_registry, "light", "bathroom2", area_id=None, device_id=device.id
    ),


async def test_area_initialization(hass, entities, devices):
    """Verify area initialization"""

    # setup component
    config: dict = {"auto_areas": {"foo": "bar"}}
    result = await async_setup_component(hass, DOMAIN, config)
    assert result is True

    # verify that areas have been registered
    auto_areas: dict[str, AutoArea] = hass.data[DOMAIN]
    assert len(auto_areas) is 4

    # verify entities
    assert len(auto_areas["kitchen"].entities) is 0
    assert len(auto_areas["living_room"].entities) is 2
    assert len(auto_areas["bedroom"].entities) is 2
    assert len(auto_areas["bathroom"].entities) is 1
