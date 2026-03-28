"""Core area functionality."""
from __future__ import annotations
from collections.abc import Callable

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.event import async_call_later
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
        self._registry_unsubs: list[Callable[[], None]] = []
        self._known_entity_ids: set[str] = set()
        self._reload_debounce_cancel: CALLBACK_TYPE | None = None

    async def async_initialize(self):
        """Subscribe to area changes and reload if necessary."""
        LOGGER.info(
            "%s: Initializing after HA start",
            self.area_name
        )
        self.auto_lights = AutoLights(self)
        await self.auto_lights.initialize()

        self._known_entity_ids = {
            e.entity_id for e in self.get_valid_entities()
        }

        self._registry_unsubs.append(
            self.hass.bus.async_listen(
                "entity_registry_updated",
                self._handle_entity_registry_updated,
            )
        )
        self._registry_unsubs.append(
            self.hass.bus.async_listen(
                "area_registry_updated",
                self._handle_area_registry_updated,
            )
        )

    async def _handle_entity_registry_updated(self, event: Event) -> None:
        """Reload when entities in this area change."""
        data = event.data
        if data.get("action") not in ("create", "update", "remove"):
            return
        entity_id = data.get("entity_id", "")
        entity = self.entity_registry.async_get(entity_id)
        if entity is None:
            # Entity was removed — only reload if it belonged to this area
            if data.get("action") == "remove" and entity_id in self._known_entity_ids:
                LOGGER.debug(
                    "%s: Known entity %s removed, scheduling reload",
                    self.area_name,
                    entity_id,
                )
                self._known_entity_ids.discard(entity_id)
                await self._schedule_reload()
            return
        # Skip our own entities to avoid infinite reload loops
        if entity.platform == DOMAIN:
            return
        from .ha_helpers import get_area_id
        if get_area_id(entity, self.device_registry) == self.area_id:
            LOGGER.debug(
                "%s: Entity registry change for %s, scheduling reload",
                self.area_name,
                entity_id,
            )
            await self._schedule_reload()

    async def _handle_area_registry_updated(self, event: Event) -> None:
        """Reload when this area is updated."""
        if event.data.get("area_id") == self.area_id:
            LOGGER.debug(
                "%s: Area registry updated, scheduling reload",
                self.area_name,
            )
            await self._schedule_reload()

    async def _schedule_reload(self) -> None:
        """Schedule a debounced reload."""
        if self._reload_debounce_cancel:
            self._reload_debounce_cancel()
        self._reload_debounce_cancel = async_call_later(
            self.hass,
            0.2,
            self._do_reload,
        )

    async def _do_reload(self, _now=None) -> None:
        """Execute the actual reload."""
        self._reload_debounce_cancel = None
        self._known_entity_ids = {
            e.entity_id for e in self.get_valid_entities()
        }
        LOGGER.debug("%s: Reloading config entry", self.area_name)
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug(
            "%s: Disabling area control",
            self.area_name
        )
        if self._reload_debounce_cancel:
            self._reload_debounce_cancel()
            self._reload_debounce_cancel = None
        for unsub in self._registry_unsubs:
            unsub()
        self._registry_unsubs.clear()
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
