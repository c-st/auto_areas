"""Illuminance sensor."""

from functools import cached_property
from typing import Any, override

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import LIGHT_LUX

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.auto_entity import AutoEntity
from custom_components.auto_areas.const import (
    ILLUMINANCE_SENSOR_ENTITY_PREFIX,
    ILLUMINANCE_SENSOR_PREFIX
)


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

    @override
    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return LIGHT_LUX

    @override
    @cached_property
    def suggested_display_precision(self) -> int | None:
        """Set the suggested precision (0)."""
        return 0

    @property
    def state(self) -> Any:  # type: ignore
        """Return the state of the entity."""
        return self._aggregated_state
