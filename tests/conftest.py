"""Fixtures for testing."""
from uuid import uuid4
from collections import OrderedDict

import logging
import asyncio
import pytest

from pytest_bdd import parsers
from pytest_bdd.steps import given, then, when

from pytest_homeassistant_custom_component.common import (
    mock_area_registry,
    mock_device_registry,
    mock_registry,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.setup import async_setup_component
from homeassistant.util import slugify
from homeassistant.helpers import (
    device_registry as dev_reg,
    entity_registry as ent_reg,
)
from custom_components.auto_areas.auto_lights import AutoLights

from custom_components.auto_areas.const import (
    DATA_AUTO_AREA,
    DOMAIN,
)
from custom_components.auto_areas.ha_helpers import get_data

AREAS = ("Kitchen", "Living Room", "Bathroom", "Bedroom")

_LOGGER = logging.getLogger(__name__)


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


@pytest.fixture(name="default_areas")
def fixture_default_areas(hass: HomeAssistant) -> dict:
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


@pytest.fixture(name="auto_areas")
async def fixture_auto_areas(hass):
    _LOGGER.info("Initializing AutoAreas fixture")
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    return get_data(hass, DATA_AUTO_AREA)


@given(parsers.parse("There are the following areas:\n{text}"), target_fixture="areas")
def fixture_create_areas(hass, text: str) -> dict:
    area_registry = mock_area_registry(hass)
    areas = OrderedDict()
    for area in text.split("\n"):
        area = slugify(area)
        created_area = area_registry.async_create(area)
        areas[slugify(area)] = created_area

    return areas


@given(
    parsers.parse("There are motion sensors placed in these areas:\n{text}"),
    target_fixture="motion_sensors",
)
def fixture_create_motion_sensors(entity_registry, areas, text: str) -> dict:
    motion_sensors = []
    for area in text.split("\n"):
        area = slugify(area)
        entity = create_entity(
            entity_registry,
            domain="binary_sensor",
            device_class="motion",
            area_id=areas[area].id,
        )
        motion_sensors.append(entity)

    return motion_sensors


@given(
    parsers.parse("There are lights placed in these areas:\n{text}"),
    target_fixture="lights",
)
def fixture_create_lights(hass, entity_registry, areas, text: str) -> dict:
    lights = []
    for area in text.split("\n"):
        area = slugify(area)
        entity = create_entity(
            entity_registry,
            domain="light",
            area_id=areas[area].id,
        )
        lights.append(entity)

    for entity in lights:
        hass.states.async_set(entity.entity_id, STATE_OFF)

    asyncio.run(hass.async_block_till_done())

    return lights


@given(parsers.parse("The state of all motion sensors is '{state}'"))
def fixture_set_entity_state(hass, motion_sensors, state):
    for entity in motion_sensors:
        hass.states.async_set(entity.entity_id, state)

    asyncio.run(hass.async_block_till_done())


@given(parsers.parse("entity states are evaluated"))
@when(parsers.parse("entity states are evaluated"))
@when(parsers.parse("component is started"))
def ensure_initialization(
    hass,
    auto_areas,
):
    """Hook to initalize AutoAreas"""
    return


@when(parsers.parse("state of motion sensor {index:d} is set to '{state}'"))
def fixture_set_motion_sensor_state(hass, motion_sensors, index, state):
    sensor = motion_sensors[index - 1]
    _LOGGER.info("Setting state of %s to %s", sensor.entity_id, state)
    hass.states.async_set(sensor.entity_id, state)
    asyncio.run(hass.async_block_till_done())


@then(parsers.parse("presence is detected in area '{area}'"))
def expect_presence(hass, auto_areas, area):
    assert hass.states.get(f"binary_sensor.auto_presence_{area}").state is STATE_ON


@then(parsers.parse("no presence is detected in area '{area}'"))
def expect_no_presence(hass: HomeAssistant, auto_areas, area):
    assert hass.states.get(f"binary_sensor.auto_presence_{area}").state is STATE_OFF


@then(parsers.parse("lights are on in area '{area}'"))
def expect_lights(hass: HomeAssistant, auto_areas, area):
    area = slugify(area)
    auto_lights: AutoLights = auto_areas[area].auto_lights
    light_states = [
        hass.states.get(entity.entity_id) for entity in auto_lights.light_entities
    ]
    assert len(light_states) > 0
    assert all(state.state in STATE_ON for state in light_states)


@then(parsers.parse("lights are off in area '{area}'"))
def expect_no_lights(hass: HomeAssistant, auto_areas, area):
    area = slugify(area)
    auto_lights: AutoLights = auto_areas[area].auto_lights
    light_states = [
        hass.states.get(entity.entity_id) for entity in auto_lights.light_entities
    ]
    assert len(light_states) > 0
    assert all(state.state in STATE_OFF for state in light_states)
