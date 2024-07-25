"""Sensor platform for auto_areas."""

from functools import cached_property
from typing import override

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import LIGHT_LUX, PERCENTAGE

from .auto_entity import AutoEntity

from .auto_area import AutoArea
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    # only setup if there is at least one sensor
    async_add_entities([IlluminanceSensor(hass, auto_area)])
    async_add_entities([TemperatureSensor(hass, auto_area)])
    async_add_entities([HumiditySensor(hass, auto_area)])


class IlluminanceSensor(
    AutoEntity[SensorEntity, SensorDeviceClass], SensorEntity
):
    """Set up aggregated illuminance sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize sensor."""
        super().__init__(
            hass,
            auto_area,
            SensorDeviceClass.ILLUMINANCE,
            (SensorDeviceClass.ILLUMINANCE,),
            "illuminance",
            "illuminance",
            "Illuminance",
        )

    @cached_property
    @override
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurment."""
        return LIGHT_LUX


class TemperatureSensor(AutoEntity[SensorEntity, SensorDeviceClass], SensorEntity):
    """Set up aggregated temperature sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize sensor."""
        super().__init__(hass,
                         auto_area,
                         SensorDeviceClass.TEMPERATURE,
                         (SensorDeviceClass.TEMPERATURE,),
                         "temperature",
                         "temperature",
                         "Temperature")

    @cached_property
    @override
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurment."""
        return self._hass.config.units.temperature_unit


class HumiditySensor(AutoEntity[SensorEntity, SensorDeviceClass], SensorEntity):
    """Set up aggregated temperature sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize sensor."""
        super().__init__(hass,
                         auto_area,
                         SensorDeviceClass.TEMPERATURE,
                         (SensorDeviceClass.TEMPERATURE,),
                         "humidity",
                         "humidity",
                         "Humidity")

    @cached_property
    @override
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurment."""
        return PERCENTAGE
