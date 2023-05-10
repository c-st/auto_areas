"""Core entity functionality."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry
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

        self.area_registry = hass.helpers.area_registry.async_get(self.hass)
        self.device_registry = self.hass.helpers.device_registry.async_get(self.hass)
        self.entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)

        self.area_id: str = entry.data.get("area")
        self.area: AreaEntry = self.area_registry.async_get_area(self.area_id)

        LOGGER.info('🤖 Auto Area "%s" (%s)', entry.title, entry.options)

        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize()
            )

    async def initialize(self):
        """Collect all entities for this area."""
        self.entities = self.get_valid_entities()
        LOGGER.info("%s Found %i relevant entities", self.area_id, len(self.entities))
        for entity in self.entities:
            LOGGER.info(
                "- %s %s (device_class: %s)",
                self.area_id,
                entity.entity_id,
                entity.device_class or entity.original_device_class,
            )

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
