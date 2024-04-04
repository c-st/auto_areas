"""Core entity functionality."""
from __future__ import annotations
from homeassistant.core import HomeAssistant

from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry

from .auto_lights import AutoLights

from .ha_helpers import get_all_entities, is_valid_entity

from .const import LOGGER, RELEVANT_DOMAINS


class AutoAreasError(Exception):
    """Exception to indicate a general API error."""


class AutoArea:
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = entry

        self.area_registry = self.hass.helpers.area_registry.async_get(self.hass)
        self.device_registry = self.hass.helpers.device_registry.async_get(self.hass)
        self.entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)

        self.area_id: str = entry.data.get("area")
        self.area: AreaEntry = self.area_registry.async_get_area(self.area_id)

        LOGGER.info('🤖 Auto Area "%s" (%s)', entry.title, entry.options)


    async def initialize(self):
        """Subscribe to area changes and reload if necessary."""
        LOGGER.info("%s: Initializing after HA start", self.area.name)

        self.auto_lights = AutoLights(self)
        await self.auto_lights.initialize()

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug("%s: Disabling area control", self.area.name)
        self.auto_lights.cleanup()

    def get_valid_entities(self) -> list[RegistryEntry]:
        """Return all valid and relevant entities for this area."""
        entities = [
            entity
            for entity in get_all_entities(
                self.entity_registry,
                self.device_registry,
                self.area_id,
                RELEVANT_DOMAINS,
            )
            if is_valid_entity(self.hass, entity)
        ]
        return entities
