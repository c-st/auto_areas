"""Core area functionality."""
from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.issue_registry import async_create_issue, IssueSeverity
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry

from .auto_lights import AutoLights

from .ha_helpers import get_all_entities, is_valid_entity

from .const import (
    CONFIG_AREA,
    DOMAIN,
    ISSUE_TYPE_INVALID_AREA,
    LOGGER,
    RELEVANT_DOMAINS,
    NAME,
    VERSION
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

        self.area_id: str | None = entry.data.get(CONFIG_AREA, None)
        self.area: AreaEntry | None = self.area_registry.async_get_area(
            self.area_id or ""
        )
        if self.area_id is None or self.area is None:
            async_create_issue(
                hass,
                DOMAIN,
                f"{ISSUE_TYPE_INVALID_AREA}_{entry.entry_id}",
                is_fixable=True,
                severity=IssueSeverity.ERROR,
                translation_key=ISSUE_TYPE_INVALID_AREA,
                data={
                    "entry_id": entry.entry_id
                }
            )

        self.auto_lights = None

    async def async_initialize(self):
        """Subscribe to area changes and reload if necessary."""
        LOGGER.info(
            "%s: Initializing after HA start",
            self.area_name
        )
        self.auto_lights = AutoLights(self)
        await self.auto_lights.initialize()

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug(
            "%s: Disabling area control",
            self.area_name
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
                self.area_id or "",
                RELEVANT_DOMAINS,
            )
            if is_valid_entity(self.hass, entity)
        ]
        return entities

    def get_area_entity_ids(self, device_classes: list[str]) -> list[str]:
        """Return all entity ids in a list of device classes."""
        return [
            entity.entity_id
            for entity in self.get_valid_entities()
            if entity.device_class in device_classes
            or entity.original_device_class in device_classes
        ]

    @property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": self.area_name,
        }

    @property
    def area_name(self) -> str:
        """Return area name or fallback."""
        return self.area.name if self.area is not None else "unknown"

    @property
    def slugified_area_name(self) -> str:
        """Return slugified area name or fallback."""
        return slugify(self.area.name) if self.area is not None else "unknown"
