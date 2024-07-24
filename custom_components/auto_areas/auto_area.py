"""Core entity functionality."""
from __future__ import annotations
from enum import StrEnum
from collections.abc import Callable
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.helpers.typing import StateType
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry

from .auto_lights import AutoLights

from .ha_helpers import get_all_entities, is_valid_entity

from .const import (
    CALCULATE,
    CONFIG_TEMPERATURE_CALCULATION,
    DOMAIN,
    LOGGER,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    RELEVANT_DOMAINS,
)


class AutoAreasError(Exception):
    """Exception to indicate a general API error."""


class AutoArea:
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        LOGGER.info('🤖 Auto Area "%s" (%s)', entry.title, entry.options)
        self.hass = hass
        self.config_entry = entry

        self.area_registry = async_get_area_registry(self.hass)
        self.device_registry = async_get_device_registry(self.hass)
        self.entity_registry = async_get_entity_registry(self.hass)

        self.area_id: str | None = entry.data.get("area")
        self.area: AreaEntry | None = self.area_registry.async_get_area(self.area_id or "")
        self.auto_lights = None

    async def async_initialize(self):
        """Subscribe to area changes and reload if necessary."""
        LOGGER.info("%s: Initializing after HA start", self.area.name if self.area is not None else "unknown")

        self.auto_lights = AutoLights(self)
        await self.auto_lights.initialize()

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug("%s: Disabling area control", self.area.name if self.area is not None else "unknown")
        if (self.auto_lights):
            self.auto_lights.cleanup()

    def get_valid_entities(self, device_class: tuple[StrEnum, ...] | None = None) -> list[RegistryEntry]:
        """Return all valid and relevant entities for this area."""
        entities = [
            entity
            for entity in get_all_entities(
                self.entity_registry,
                self.device_registry,
                self.area_id,
                RELEVANT_DOMAINS,
            )
            if is_valid_entity(self.hass, entity) and (
                device_class is None or ((
                    entity.device_class in device_class or entity.original_device_class in device_class
                    ) and entity.platform != DOMAIN)
            )
        ]
        return entities

    def get_valid_entity_ids(self, device_class: tuple[StrEnum, ...] | None = None) -> list[str]:
        """Return all valid and relevant entity ids for this area."""
        return [
            entity.entity_id
            for entity
            in self.get_valid_entities(device_class)
        ]

    def get_calculation(self, sensor_type: BinarySensorDeviceClass | SensorDeviceClass) -> Callable[[list[State]], StateType] | None:
        """Get the configured calculation for the sensor provided."""
        if sensor_type in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES:
            return None  # TODO
        if sensor_type == SensorDeviceClass.TEMPERATURE:
            return CALCULATE[self.config_entry.options[CONFIG_TEMPERATURE_CALCULATION]]
        if sensor_type == SensorDeviceClass.ILLUMINANCE:
            return CALCULATE[self.config_entry.options[CONFIG_TEMPERATURE_CALCULATION]]
        if sensor_type == SensorDeviceClass.HUMIDITY:
            return CALCULATE[self.config_entry.options[CONFIG_TEMPERATURE_CALCULATION]]
        return None
