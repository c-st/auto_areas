from homeassistant.setup import async_setup_component

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import DATA_AUTO_AREA, DOMAIN
from custom_components.auto_areas.ha_helpers import get_data


async def test_fails_with_wrong_configuration(hass):
    config: dict = {"auto_areas": {"bedroom": {"foo": False}}}
    result = await async_setup_component(hass, DOMAIN, config)
    assert result is False


async def test_copies_configuration_to_auto_area(hass, default_entities):
    config: dict = {"auto_areas": {"bedroom": {"is_sleeping_area": True}}}
    result = await async_setup_component(hass, DOMAIN, config)
    assert result is True

    # verify that config has been copied to auto_area
    auto_areas: dict[str, AutoArea] = get_data(hass, DATA_AUTO_AREA)
    assert auto_areas["bedroom"].config.get("is_sleeping_area") is True
