"""Cover group."""

from functools import cached_property
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.group.cover import CoverGroup
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.cover import (
    CoverDeviceClass,
    DEVICE_CLASSES as COVER_DEVICE_CLASSES,
)

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import (
    COVER_GROUP_ENTITY_PREFIX,
    COVER_GROUP_PREFIX,
    DOMAIN,
    LOGGER,
    NAME,
    VERSION
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the cover platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]

    cover_entity_ids: list[str] = auto_area.get_area_entity_ids(
        COVER_DEVICE_CLASSES
    )
    if not cover_entity_ids:
        LOGGER.info(
            "%s: No covers found in area. Not creating cover group.",
            auto_area.area_name,
        )
    else:
        async_add_entities([AutoCoverGroup(
            hass,
            auto_area,
            entity_ids=cover_entity_ids
        )])


class AutoCoverGroup(CoverGroup):
    """Cover group with area covers."""

    def __init__(self, hass, auto_area: AutoArea, entity_ids: list[str]) -> None:
        """Initialize cover group."""
        self.hass = hass
        self.auto_area = auto_area
        self._device_class = CoverDeviceClass.BLIND
        self._name_prefix = COVER_GROUP_PREFIX
        self._prefix = COVER_GROUP_ENTITY_PREFIX
        self.entity_ids: list[str] = entity_ids

        CoverGroup.__init__(
            self,
            entities=self.entity_ids,
            name=None,
            unique_id=self._attr_unique_id,
        )

        LOGGER.debug("Initialized cover group %s", self.entity_ids)

    @cached_property
    def name(self):
        """Name of this entity."""
        return f"{self._name_prefix}{self.auto_area.area_name}"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": self.auto_area.area_name,
        }

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_cover_group"
