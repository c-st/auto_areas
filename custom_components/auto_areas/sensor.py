"""Sensor platform for auto_areas."""

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.auto_areas.sensors.humidity import HumiditySensor
from custom_components.auto_areas.sensors.illuminance import IlluminanceSensor
from custom_components.auto_areas.sensors.temperature import TemperatureSensor


from .auto_area import AutoArea
from .const import (
    DOMAIN,
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        IlluminanceSensor(hass, auto_area),
        TemperatureSensor(hass, auto_area),
        HumiditySensor(hass, auto_area)
    ])
