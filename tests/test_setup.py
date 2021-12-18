import logging

from homeassistant.setup import async_setup_component
from custom_components.auto_areas.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def test_async_setup(hass):
    """Test the component gets setup."""
    result = await async_setup_component(hass, DOMAIN, {"auto_areas": {"foo": "bar"}})
    assert result is True
