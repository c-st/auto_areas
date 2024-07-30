"""Sleep mode switch."""
from __future__ import annotations
from functools import cached_property

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import UndefinedType

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.const import (
    LOGGER,
    SLEEP_MODE_SWITCH_PREFIX
)


class SleepModeSwitch(SwitchEntity):
    """Set up a sleep mode switch."""

    _attr_should_poll = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize sleep mode switch."""
        self.auto_area = auto_area
        self._is_on: bool = False
        LOGGER.info(
            "%s: Initialized sleep mode switch (%s)",
            self.auto_area.area_name,
            self.name
        )

    @cached_property
    def name(self) -> str | UndefinedType | None:
        """Return the name of the entity."""
        return f"{SLEEP_MODE_SWITCH_PREFIX}{self.auto_area.area_name}"

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_sleep_mode"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return self.auto_area.device_info

    @cached_property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    @property
    def is_on(self) -> bool | None:
        """Return the state of the switch."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        LOGGER.info("%s: Sleep mode turned on", self.auto_area.area_name)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off switch."""
        LOGGER.info("%s: Sleep mode turned off", self.auto_area.area_name)
        self._is_on = False
        self.schedule_update_ha_state()
