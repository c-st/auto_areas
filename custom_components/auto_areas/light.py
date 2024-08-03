"""Light group."""

from functools import cached_property
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.group.light import LightGroup
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import (
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
    DOMAIN,
    EXCLUDED_DOMAINS,
    LIGHT_GROUP_ENTITY_PREFIX,
    LIGHT_GROUP_PREFIX,
    LOGGER
)

from .ha_helpers import get_all_entities


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the light platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    excluded_light_entities = excluded_light_entities = (
        auto_area.config_entry.options.get(
            CONFIG_EXCLUDED_LIGHT_ENTITIES)
        or []
    )
    light_entity_ids = [
        entity.entity_id
        for entity in get_all_entities(
            auto_area.entity_registry,
            auto_area.device_registry,
            auto_area.area_id,
            [LIGHT_DOMAIN],
        )
        if entity.entity_id not in excluded_light_entities
        and entity.platform not in EXCLUDED_DOMAINS
    ]

    if not light_entity_ids:
        LOGGER.info(
            "%s: No lights found in area. Not creating light group.",
            auto_area.area_name,
        )
    else:
        async_add_entities([AutoLightGroup(
            hass,
            auto_area,
            entity_ids=light_entity_ids
        )])


class AutoLightGroup(LightGroup):
    """Cover group with area covers."""

    def __init__(self, hass, auto_area: AutoArea, entity_ids: list[str]) -> None:
        """Initialize cover group."""
        self.hass = hass
        self.auto_area = auto_area
        self._name_prefix = LIGHT_GROUP_PREFIX
        self._prefix = LIGHT_GROUP_ENTITY_PREFIX
        self.entity_ids: list[str] = entity_ids

        LightGroup.__init__(
            self,
            unique_id=self._attr_unique_id,
            name=None,
            entity_ids=self.entity_ids,
            mode=None
        )
        LOGGER.info(
            "%s (%s): Initialized light group. Entities: %s",
            self.auto_area.area_name,
            self.device_class,
            self.entity_ids
        )

    @cached_property
    def name(self):
        """Name of this entity."""
        return f"{self._name_prefix}{self.auto_area.area_name}"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return self.auto_area.device_info

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_light_group"
