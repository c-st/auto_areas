"""Core area functionality."""
from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.issue_registry import async_create_issue as async_create_issue, IssueSeverity
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry

from .auto_lights import AutoLights

from .ha_helpers import get_all_entities, is_valid_entity

from .const import (
    CONFIG_AREA,
    DOMAIN,
    LOGGER,
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

        area_id = entry.data.get(CONFIG_AREA)
        area = self.area_registry.async_get_area(area_id or "")
        if area_id is None or area is None:
            async_create_issue(
                hass,
                DOMAIN,
                f"invalid_area_config_{entry.entry_id}",
                is_fixable=True,
                severity=IssueSeverity.ERROR,
                translation_key="invalid_area_config",
                data={
                    "entry_id": entry.entry_id
                }
            )
            return

        self.area_id: str = area_id
        self.area: AreaEntry = area
        self.auto_lights = None

    async def async_initialize(self):
        """Subscribe to area changes and reload if necessary."""
        LOGGER.info(
            "%s: Initializing after HA start",
            self.area.name
        )

        self.auto_lights = AutoLights(self)
        await self.auto_lights.initialize()

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug(
            "%s: Disabling area control",
            self.area.name
        )
        if self.auto_lights:
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

    @property
    def area_name(self) -> str:
        """Return area name or fallback."""
        return self.area.name if self.area is not None else "unknown"
