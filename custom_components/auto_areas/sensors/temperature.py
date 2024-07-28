"""Temperature sensor."""

from functools import cached_property
from typing import Any, override

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.auto_entity import AutoEntity
from custom_components.auto_areas.const import TEMPERATURE_SENSOR_ENTITY_PREFIX, TEMPERATURE_SENSOR_PREFIX


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

    @override
    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return self.hass.config.units.temperature_unit

    @override
    @property
    def state(self) -> Any:  # type: ignore
        """Return the state of the entity."""
        return self._aggregated_state
