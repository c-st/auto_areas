"""Tests for verifying component setup"""
from homeassistant.setup import async_setup_component

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import DOMAIN

from tests.conftest import create_entity


async def test_presence_state_tracking(hass, entity_registry, default_entities):
    """Verify that only entities from supported domains are registered"""
    bedroom_sensor = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bedroom",
    )
    bedroom_sensor2 = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bedroom",
    )
    bathroom_sensor = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bathroom",
    )

    await async_setup_component(hass, DOMAIN, {})
    auto_areas: dict[str, AutoArea] = hass.data[DOMAIN]

    # verify entities amount
    assert len(auto_areas["bedroom"].entities) is 3
    assert len(auto_areas["bathroom"].entities) is 2
    assert auto_areas["bathroom"].presence is False
    assert auto_areas["bedroom"].presence is False

    # set initial state
    hass.states.async_set(bathroom_sensor.entity_id, "off")
    hass.states.async_set(bedroom_sensor.entity_id, "off")
    hass.states.async_set(bedroom_sensor2.entity_id, "off")
    await hass.async_block_till_done()

    # motion detected
    hass.states.async_set(bedroom_sensor2.entity_id, "on")
    await hass.async_block_till_done()

    # presence state should be set
    assert auto_areas["bathroom"].presence is False
    assert auto_areas["bedroom"].presence is True


async def test_clears_presence_state(hass, entity_registry, default_entities):
    """Make sure that presence is cleared"""
    bedroom_sensor = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bedroom",
    )
    bedroom_sensor2 = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bedroom",
    )

    await async_setup_component(hass, DOMAIN, {})
    auto_areas: dict[str, AutoArea] = hass.data[DOMAIN]
    hass.states.async_set(bedroom_sensor.entity_id, "on")
    hass.states.async_set(bedroom_sensor2.entity_id, "off")
    await hass.async_block_till_done()
    assert auto_areas["bedroom"].presence is True

    # presence off
    hass.states.async_set(bedroom_sensor.entity_id, "off")
    await hass.async_block_till_done()

    # presence state should be cleared
    assert auto_areas["bedroom"].presence is False


async def test_evaluates_all_entities_initially(
    hass, entity_registry, default_entities
):
    """Set presence based on state of all sensors initially"""
    bedroom_sensor = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bedroom",
    )
    bedroom_sensor2 = create_entity(
        entity_registry,
        domain="binary_sensor",
        device_class="motion",
        area_id="bedroom",
    )

    hass.states.async_set(bedroom_sensor.entity_id, "on")
    hass.states.async_set(bedroom_sensor2.entity_id, "off")
    await hass.async_block_till_done()

    await async_setup_component(hass, DOMAIN, {})
    auto_areas: dict[str, AutoArea] = hass.data[DOMAIN]

    # initial presence should be detected (without state change)
    assert auto_areas["bedroom"].presence is True
