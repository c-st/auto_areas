"""
Tests for verifying component setup

(partially converted to BDD scenarios)
"""

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import (
    DATA_AUTO_AREA,
    DOMAIN,
)
from custom_components.auto_areas.ha_helpers import get_data

from tests.conftest import create_entity


async def test_presence_state_tracking(
    hass: HomeAssistant, entity_registry, default_entities
):
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
    await hass.async_block_till_done()
    auto_areas: dict[str, AutoArea] = get_data(hass, DATA_AUTO_AREA) or {}

    # verify entities amount
    assert len(auto_areas["bedroom"].entities) is 3
    assert len(auto_areas["bathroom"].entities) is 2

    assert hass.states.get("binary_sensor.auto_presence_bathroom").state is STATE_OFF
    assert hass.states.get("binary_sensor.auto_presence_bedroom").state is STATE_OFF

    # set initial state
    hass.states.async_set(bathroom_sensor.entity_id, STATE_OFF)
    hass.states.async_set(bedroom_sensor.entity_id, STATE_OFF)
    hass.states.async_set(bedroom_sensor2.entity_id, STATE_OFF)
    await hass.async_block_till_done()

    # motion detected
    hass.states.async_set(bedroom_sensor2.entity_id, STATE_ON)
    await hass.async_block_till_done()

    # presence state should be set
    print(hass.states)
    assert hass.states.get("binary_sensor.auto_presence_bathroom").state is STATE_OFF
    assert hass.states.get("binary_sensor.auto_presence_bedroom").state is STATE_ON


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
    hass.states.async_set(bedroom_sensor.entity_id, STATE_ON)
    hass.states.async_set(bedroom_sensor2.entity_id, STATE_OFF)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.auto_presence_bedroom").state is STATE_ON

    # presence off
    hass.states.async_set(bedroom_sensor.entity_id, STATE_OFF)
    await hass.async_block_till_done()

    # presence state should be cleared
    assert hass.states.get("binary_sensor.auto_presence_bedroom").state is STATE_OFF


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

    hass.states.async_set(bedroom_sensor.entity_id, STATE_ON)
    hass.states.async_set(bedroom_sensor2.entity_id, STATE_OFF)
    await hass.async_block_till_done()

    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    # initial presence should be detected (without state change)
    assert hass.states.get("binary_sensor.auto_presence_bedroom").state is STATE_ON
