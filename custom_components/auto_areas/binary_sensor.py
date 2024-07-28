"""Binary sensor platform for auto_areas."""

from __future__ import annotations

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from custom_components.auto_areas.binary_sensors.presence import PresenceBinarySensor

from .auto_area import AutoArea
from .const import (
    DOMAIN,
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the binary_sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PresenceBinarySensor(hass, auto_area)])
