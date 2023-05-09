"""Core entity functionality."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, STATE_UNAVAILABLE
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.entity_registry import RegistryEntry
from .ha_helpers import get_all_entities

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

        self.area_id = entry.data.get("area")
        self.area = self.area_registry.async_get_area(self.area_id)

        LOGGER.info('🤖 Auto Area "%s" (%s)', entry.title, entry.options)

        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize()
            )

    async def initialize(self):
        """Collect all entities for this area."""
        entities = get_all_entities(
            self.entity_registry,
            self.device_registry,
            self.area_id,
            RELEVANT_DOMAINS,
        )
        self.entities = [entity for entity in entities if self.is_valid_entity(entity)]
        LOGGER.info("%s Found %i relevant entities", self.area_id, len(self.entities))
        for entity in self.entities:
            LOGGER.info(
                "- %s %s (device_class: %s)",
                self.area_id,
                entity.entity_id,
                entity.device_class or entity.original_device_class,
            )

    def is_valid_entity(self, entity: RegistryEntry) -> bool:
        """Check whether an entity should be included."""
        if entity.disabled:
            return False

        entity_state = self.hass.states.get(entity.entity_id)
        if entity_state and entity_state.state == STATE_UNAVAILABLE:
            return False

        return True
