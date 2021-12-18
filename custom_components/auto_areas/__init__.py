import logging

from homeassistant.core import Config, HomeAssistant
from homeassistant.loader import async_get_integration

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration using YAML"""
    conf = config.get(DOMAIN)
    if conf is None:
        conf = {}

    hass.data[DOMAIN] = {}
    _LOGGER.info("Loaded config %s", conf)
    return True
