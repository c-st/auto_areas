"""BlueprintEntity class."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .auto_area import (
    AutoArea,
)

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION


class IntegrationBlueprintEntity(CoordinatorEntity):
    """BlueprintEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize."""

        super().__init__(auto_area)
        self._attr_unique_id = auto_area.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )
