"""Tests for verifying component setup"""
import logging
from collections import OrderedDict

import pytest
import uuid

from homeassistant.util import slugify
from homeassistant.setup import async_setup_component
from homeassistant.helpers import (
    entity_registry as ent_reg,
)

from pytest_homeassistant_custom_component.common import (
    mock_area_registry,
    mock_registry,
)
from custom_components.auto_areas.auto_area import AutoArea

from custom_components.auto_areas.const import DOMAIN

_LOGGER = logging.getLogger(__name__)
AREAS = ("Kitchen", "Living Room", "Bathroom", "Bedroom")


@pytest.fixture(name="areas")
def fixture_areas(hass) -> dict:
    """Areas"""
    area_registry = mock_area_registry(hass)
    areas = OrderedDict()
    for area in AREAS:
        created_area = area_registry.async_create(area)
        areas[slugify(area)] = created_area
    return areas


@pytest.fixture(name="entities")
def fixture_entities(hass, areas) -> dict:
    """Entities assigned to areas"""
    entities = {
        "light.entrance": ent_reg.RegistryEntry(
            entity_id="light.entrance",
            unique_id=uuid.uuid4(),
            platform="test",
        ),
        "light.bathroom": ent_reg.RegistryEntry(
            entity_id="light.bathroom",
            unique_id=uuid.uuid4(),
            platform="test",
            area_id=areas["bathroom"].id,
        ),
        "light.bedroom": ent_reg.RegistryEntry(
            entity_id="light.bedroom",
            unique_id=uuid.uuid4(),
            platform="test",
            area_id=areas["bedroom"].id,
        ),
        "light.living_room": ent_reg.RegistryEntry(
            entity_id="light.living_room",
            unique_id=uuid.uuid4(),
            platform="test",
            area_id=areas["living_room"].id,
        ),
        "light.living_room_2": ent_reg.RegistryEntry(
            entity_id="light.living_room_2",
            unique_id=uuid.uuid4(),
            platform="test",
            area_id=areas["living_room"].id,
        ),
    }

    mock_registry(
        hass,
        entities,
    )

    return entities


async def test_area_initialization(hass, areas, entities):
    """Verify area initialization"""

    # setup component
    config: dict = {"auto_areas": {"foo": "bar"}}
    result = await async_setup_component(hass, DOMAIN, config)
    assert result is True

    # verify that areas have been registered
    auto_areas: dict[str, AutoArea] = hass.data[DOMAIN]
    assert len(auto_areas) is 4

    assert len(auto_areas["kitchen"].entities) is 0
    assert len(auto_areas["living_room"].entities) is 2
    assert len(auto_areas["bathroom"].entities) is 1
    assert len(auto_areas["bedroom"].entities) is 1
