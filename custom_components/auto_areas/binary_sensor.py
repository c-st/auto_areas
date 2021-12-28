import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaRegistry
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.auto_areas.auto_presence import AutoPresenceBinarySensor
from custom_components.auto_areas.const import DOMAINS
from custom_components.auto_areas.ha_helpers import get_all_entities

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    _LOGGER.info("async_setup_entry Setup AutoPresence platform")


async def async_unload_entry(hass, entry):
    _LOGGER.info("async_unload_entry")


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Set up platform."""
    _LOGGER.info("async_setup_platform Setup AutoPresence platform")

    area_registry: AreaRegistry = await hass.helpers.area_registry.async_get_registry()
    entity_registry: EntityRegistry = (
        await hass.helpers.entity_registry.async_get_registry()
    )
    device_registry: DeviceRegistry = (
        await hass.helpers.device_registry.async_get_registry()
    )

    area_binary_sensors = []
    for area in area_registry.async_list_areas():
        area_entities = get_all_entities(
            entity_registry, device_registry, area.id, DOMAINS
        )
        area_binary_sensors.append(AutoPresenceBinarySensor(hass, area_entities, area))

    # set_data(hass, DATA_AUTO_PRESENCE, area_binary_sensors)
    async_add_entities(area_binary_sensors)

    _LOGGER.info(area_binary_sensors)
