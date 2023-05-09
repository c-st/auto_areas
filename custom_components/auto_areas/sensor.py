"""Sensor platform for integration_blueprint."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .auto_area import AutoArea
from .entity import IntegrationBlueprintEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="integration_blueprint",
        name="Integration Sensor",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    # auto_area = hass.data[DOMAIN][entry.entry_id]
    # async_add_devices(
    #     IntegrationBlueprintSensor(
    #         coordinator=coordinator,
    #         entity_description=entity_description,
    #     )
    #     for entity_description in ENTITY_DESCRIPTIONS
    # )


class IntegrationBlueprintSensor(IntegrationBlueprintEntity, SensorEntity):
    """integration_blueprint Sensor class."""

    def __init__(
        self,
        auto_area: AutoArea,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(auto_area)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self.coordinator.data.get("body")
