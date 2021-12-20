"""Tests for verifying component setup"""
import logging
from collections import OrderedDict

import uuid
import pytest

from homeassistant.util import slugify
from homeassistant.setup import async_setup_component
from homeassistant.helpers import (
    device_registry,
    entity_registry as ent_reg,
)

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_area_registry,
    mock_device_registry,
    mock_registry,
)
from custom_components.auto_areas.auto_area import AutoArea

from custom_components.auto_areas.const import DOMAIN

_LOGGER = logging.getLogger(__name__)
AREAS = ("Kitchen", "Living Room", "Bathroom", "Bedroom")


@pytest.fixture(name="areas", autouse=True)
def fixture_areas(hass) -> dict:
    """Areas"""
    area_registry = mock_area_registry(hass)
    areas = OrderedDict()
    for area in AREAS:
        created_area = area_registry.async_create(area)
        areas[slugify(area)] = created_area

    return areas


@pytest.fixture(name="entity_registry")
def fixture_entity_registry(hass, areas) -> ent_reg.EntityRegistry:
    """Entities assigned to areas"""
    entities = {
        "light.entrance": ent_reg.RegistryEntry(
            entity_id="light.entrance",
            unique_id=str(uuid.uuid4()),
            platform="test",
        ),
        "light.bathroom": ent_reg.RegistryEntry(
            entity_id="light.bathroom",
            unique_id=str(uuid.uuid4()),
            platform="test",
            area_id=areas["bathroom"].id,
        ),
        "light.bedroom": ent_reg.RegistryEntry(
            entity_id="light.bedroom",
            unique_id=str(uuid.uuid4()),
            platform="test",
            area_id=areas["bedroom"].id,
        ),
        "light.living_room": ent_reg.RegistryEntry(
            entity_id="light.living_room",
            unique_id=str(uuid.uuid4()),
            platform="test",
            area_id=areas["living_room"].id,
        ),
        "light.living_room_2": ent_reg.RegistryEntry(
            entity_id="light.living_room_2",
            unique_id=str(uuid.uuid4()),
            platform="test",
            area_id=areas["living_room"].id,
        ),
    }
    return mock_registry(
        hass,
        entities,
    )


@pytest.fixture(name="devices")
async def fixture_devices(hass, areas, entity_registry: ent_reg.EntityRegistry) -> None:
    """Entity which is assigned to an area via a device"""
    registry = mock_device_registry(hass)
    bedroom_area_id = areas["bedroom"].id
    config_entry = MockConfigEntry(domain="light")

    # Create device
    device = registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        entry_type=device_registry.DeviceEntryType.SERVICE,
        sw_version="sw-version",
        name="name",
        manufacturer="manufacturer",
        model="model",
    )
    registry.async_update_device(device.id, area_id=bedroom_area_id)

    # Create entity for device
    entity_registry.async_get_or_create(
        "light",
        "hue",
        str(uuid.uuid4()),
        device_id=device.id,
    )


async def test_area_initialization(hass, areas, entity_registry, devices):
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
    assert len(auto_areas["bathroom"].entities) is 1
    assert len(auto_areas["bedroom"].entities) is 2
