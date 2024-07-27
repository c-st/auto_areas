"""Binary sensor platform for auto_areas."""

from __future__ import annotations

from functools import cached_property

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .auto_entity import AutoEntity

from .auto_area import AutoArea
from .const import (
    DOMAIN,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the binary_sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PresenceBinarySensor(hass, auto_area)])


class PresenceBinarySensor(
    AutoEntity[BinarySensorEntity, BinarySensorDeviceClass], BinarySensorEntity
):
    """Set up aggregated presence binary sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize presence lo1ck switch."""
        super().__init__(
            hass,
            auto_area,
            BinarySensorDeviceClass.OCCUPANCY,
            PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
            "presence",
            "presence",
            "Presence",
        )

    @cached_property
    def is_on(self) -> bool:
        """Return the presence state."""
        return self._attr_state == 'on' if isinstance(self._attr_state, bool) else False
