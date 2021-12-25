"""Fixtures for testing."""
from collections import OrderedDict
import logging
from typing import List
from homeassistant.util import slugify, uuid
import pytest
from uuid import uuid4

from pytest_homeassistant_custom_component.common import (
    mock_area_registry,
    mock_device_registry,
    mock_registry,
)
from homeassistant.helpers import (
    device_registry as dev_reg,
    entity_registry as ent_reg,
)

AREAS = ("Kitchen", "Living Room", "Bathroom", "Bedroom")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Required for testing integration"""
    yield


@pytest.fixture(name="device_registry")
def fixture_device_registry(hass) -> dev_reg.DeviceRegistry:
    """Provide a mock device registry"""
    return mock_device_registry(hass)


@pytest.fixture(name="entity_registry")
def fixture_entity_registry(hass) -> ent_reg.EntityRegistry:
    """Entities assigned to areas"""
    default_entities = {
        "light.entrance": ent_reg.RegistryEntry(
            entity_id="light.entrance",
            unique_id="entrance1",
            platform="test",
        ),
        "light.entrance2": ent_reg.RegistryEntry(
            entity_id="light.entrance2",
            unique_id="entrance2",
            platform="test",
        ),
    }
    return mock_registry(
        hass,
        default_entities,
    )


@pytest.fixture(name="default_areas", autouse=True)
def fixture_default_areas(hass) -> dict:
    """Create and provide Areas"""
    area_registry = mock_area_registry(hass)
    areas = OrderedDict()
    for area in AREAS:
        created_area = area_registry.async_create(area)
        areas[slugify(area)] = created_area

    return areas


@pytest.fixture(name="default_entities")
def fixture_default_entities(default_areas, entity_registry) -> None:
    """Default entities assigned to areas"""
    create_entity(entity_registry, domain="light", unique_id="1", area_id="living_room")
    create_entity(entity_registry, domain="light", unique_id="2", area_id="living_room")
    create_entity(entity_registry, domain="light", unique_id="1", area_id="bedroom")
    create_entity(entity_registry, domain="light", unique_id="1", area_id="bathroom")


def create_entity(
    entity_registry: ent_reg.EntityRegistry,
    domain: str,
    unique_id: str = None,
    area_id: str = None,
    device_id: str = None,
    device_class: str = None,
) -> ent_reg.RegistryEntry:
    """Inserts a fake entity into registry"""

    if unique_id is None:
        unique_id = str(uuid4())

    entity = entity_registry.async_get_or_create(
        domain=domain,
        unique_id=unique_id,
        platform=area_id,
        area_id=area_id,
        device_id=device_id,
    )

    if device_class is not None:
        entity_registry.async_update_entity(entity.entity_id, device_class=device_class)

    return entity
