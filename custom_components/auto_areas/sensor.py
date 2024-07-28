"""Sensor platform for auto_areas."""

from functools import cached_property
from typing import Any, override

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import LIGHT_LUX, PERCENTAGE

from .auto_entity import AutoEntity

from .auto_area import AutoArea
from .const import DOMAIN, HUMIDITY_SENSOR_ENTITY_PREFIX, HUMIDITY_SENSOR_PREFIX, ILLUMINANCE_SENSOR_ENTITY_PREFIX, ILLUMINANCE_SENSOR_PREFIX, TEMPERATURE_SENSOR_ENTITY_PREFIX, TEMPERATURE_SENSOR_PREFIX


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        IlluminanceSensor(hass, auto_area),
        TemperatureSensor(hass, auto_area),
        HumiditySensor(hass, auto_area)
    ])


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
            ILLUMINANCE_SENSOR_PREFIX,
            ILLUMINANCE_SENSOR_ENTITY_PREFIX
        )

    @cached_property
    @override
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return LIGHT_LUX

    @cached_property
    def state(self) -> Any:  # type: ignore
        """Return the state of the entity."""
        return self._aggregated_state


class TemperatureSensor(AutoEntity[SensorEntity, SensorDeviceClass], SensorEntity):
    """Set up aggregated temperature sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize sensor."""
        super().__init__(
            hass,
            auto_area,
            SensorDeviceClass.TEMPERATURE,
            TEMPERATURE_SENSOR_PREFIX,
            TEMPERATURE_SENSOR_ENTITY_PREFIX
        )

    @cached_property
    @override
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return self.hass.config.units.temperature_unit

    @cached_property
    def state(self) -> Any:  # type: ignore
        """Return the state of the entity."""
        return self._aggregated_state


class HumiditySensor(AutoEntity[SensorEntity, SensorDeviceClass], SensorEntity):
    """Set up aggregated humidity sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize sensor."""
        super().__init__(
            hass,
            auto_area,
            SensorDeviceClass.HUMIDITY,
            HUMIDITY_SENSOR_PREFIX,
            HUMIDITY_SENSOR_ENTITY_PREFIX
        )

    @cached_property
    @override
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return PERCENTAGE

    @cached_property
    def state(self) -> Any:  # type: ignore
        """Return the state of the entity."""
        return self._aggregated_state
