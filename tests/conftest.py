"""Fixtures for testing."""
from collections import OrderedDict
import logging
from homeassistant.util import slugify
import pytest

from pytest_homeassistant_custom_component.common import (
    mock_area_registry,
    mock_device_registry,
    mock_registry,
)
from homeassistant.helpers import (
    device_registry as dev_reg,
    entity_registry as ent_reg,
)

_LOGGER = logging.getLogger(__name__)
AREAS = ("Kitchen", "Living Room", "Bathroom", "Bedroom")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Required for testing integration"""
    yield


@pytest.fixture(name="areas", autouse=True)
def fixture_areas(hass) -> dict:
    """Create and provide Areas"""
    area_registry = mock_area_registry(hass)
    areas = OrderedDict()
    for area in AREAS:
        created_area = area_registry.async_create(area)
        areas[slugify(area)] = created_area

    return areas


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


def create_entity(
    entity_registry: ent_reg.EntityRegistry,
    domain: str,
    unique_id: str,
    area_id: str = None,
    device_id: str = None,
) -> ent_reg.RegistryEntry:
    """Inserts a fake entity into registry"""
    return entity_registry.async_get_or_create(
        domain=domain,
        unique_id=unique_id,
        platform=area_id,
        area_id=area_id,
        device_id=device_id,
    )
