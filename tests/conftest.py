"""pytest fixtures."""
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er
from homeassistant.const import STATE_ON

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.auto_areas.const import DOMAIN, CONFIG_AREA


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
async def test_area(hass: HomeAssistant) -> ar.AreaEntry:
    """Create a test area in the HA area registry."""
    area_registry = ar.async_get(hass)
    return area_registry.async_create("Test Room")


@pytest.fixture
async def cover_entity(hass: HomeAssistant, test_area: ar.AreaEntry) -> str:
    """Create a mock cover entity assigned to the test area."""
    entity_registry = er.async_get(hass)

    entry = entity_registry.async_get_or_create(
        domain="cover",
        platform="test",
        unique_id="test_cover_1",
        suggested_object_id="test_blinds",
        original_device_class="blind",
    )
    entity_registry.async_update_entity(entry.entity_id, area_id=test_area.id)

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()

    return entry.entity_id


@pytest.fixture
async def light_entity(hass: HomeAssistant, test_area: ar.AreaEntry) -> str:
    """Create a mock light entity assigned to the test area."""
    entity_registry = er.async_get(hass)

    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="test",
        unique_id="test_light_1",
        suggested_object_id="test_lamp",
    )
    entity_registry.async_update_entity(entry.entity_id, area_id=test_area.id)

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()

    return entry.entity_id


@pytest.fixture
async def binary_sensor_door(hass: HomeAssistant, test_area: ar.AreaEntry) -> str:
    """Create a binary_sensor with device_class 'door' assigned to test area."""
    entity_registry = er.async_get(hass)

    entry = entity_registry.async_get_or_create(
        domain="binary_sensor",
        platform="test",
        unique_id="test_door_sensor",
        suggested_object_id="washing_machine_door",
        original_device_class="door",
    )
    entity_registry.async_update_entity(entry.entity_id, area_id=test_area.id)

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()

    return entry.entity_id


@pytest.fixture
async def motion_sensor(hass: HomeAssistant, test_area: ar.AreaEntry) -> str:
    """Create a motion sensor assigned to the test area."""
    entity_registry = er.async_get(hass)

    entry = entity_registry.async_get_or_create(
        domain="binary_sensor",
        platform="test",
        unique_id="test_motion_1",
        suggested_object_id="test_motion",
        original_device_class="motion",
    )
    entity_registry.async_update_entity(entry.entity_id, area_id=test_area.id)

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()

    return entry.entity_id


@pytest.fixture
async def config_entry(
    hass: HomeAssistant, test_area: ar.AreaEntry
) -> MockConfigEntry:
    """Create and set up a config entry for auto_areas."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONFIG_AREA: test_area.id},
        options={},
        title="Test Room",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry
