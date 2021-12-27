import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up platform."""
    _LOGGER.info("async setup platform")
    # go through all areas and setup binary_sensor for area presence
