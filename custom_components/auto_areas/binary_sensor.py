"""Binary sensor platform for auto_areas."""

from __future__ import annotations

from functools import cached_property
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.auto_areas.auto_entity import AutoEntity

from .auto_area import AutoArea
from .const import (
    DOMAIN,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_ON_STATES,
)
from .ha_helpers import all_states_are_off


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
        return self.state == 'on' if isinstance(self._attr_state, bool) else False

    @override
    def _get_state(self):
        """Handle state change of any tracked presence sensors."""
        self._attr_state = not all_states_are_off(self.hass, self.entities, PRESENCE_ON_STATES) # type: ignore
        return self._attr_state
