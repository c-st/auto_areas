"""Switch platform for integration_blueprint."""
from __future__ import annotations
from functools import cached_property

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import UndefinedType

from .auto_area import AutoArea

from .const import (
    LOGGER,
    DOMAIN,
    NAME,
    VERSION,
    CONFIG_IS_SLEEPING_AREA,
    PRESENCE_LOCK_SWITCH_PREFIX,
    SLEEP_MODE_SWITCH_PREFIX,
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the switch platform."""
    LOGGER.info("Setting up switch platform")
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]

    switch_entities: list[Entity] = [PresenceLockSwitch(auto_area)]

    if auto_area.config_entry.options.get(CONFIG_IS_SLEEPING_AREA):
        switch_entities.append(SleepModeSwitch(auto_area))

    async_add_entities(switch_entities)


class PresenceLockSwitch(SwitchEntity):
    """Set up a presence lock switch."""

    _attr_should_poll: bool = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize presence lock switch."""
        self.auto_area = auto_area
        self._is_on: bool = False
        LOGGER.info(
            "%s: Initialized presence lock switch",
            self.auto_area.area_name
        )

    @cached_property
    def name(self) -> str | UndefinedType | None:
        """Return the name of the entity."""
        return f"{PRESENCE_LOCK_SWITCH_PREFIX}{self.auto_area.area_name}"

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_presence_lock"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": getattr(self.auto_area.area, 'name', None),
        }

    @cached_property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    @cached_property
    def is_on(self) -> bool | None:
        """Return the state of the switch."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        LOGGER.info("%s: Presence lock turned on", getattr(
            self.auto_area.area, 'name', 'unknown'))
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off switch."""
        LOGGER.info("%s: Presence lock turned off", getattr(
            self.auto_area.area, 'name', 'unknown'))
        self._is_on = False
        self.schedule_update_ha_state()


class SleepModeSwitch(SwitchEntity):
    """Set up a sleep mode switch."""

    _attr_should_poll = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize sleep mode switch."""
        self.auto_area = auto_area
        self._is_on: bool = False
        LOGGER.info(
            "%s: Initialized sleep mode switch",
            self.auto_area.area_name
        )

    @cached_property
    def name(self) -> str | UndefinedType | None:
        """Return the name of the entity."""
        return f"{SLEEP_MODE_SWITCH_PREFIX}{getattr(self.auto_area.area, 'name', 'unknown')}"

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_sleep_mode"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": getattr(self.auto_area.area, 'name', None),
        }

    @cached_property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    @cached_property
    def is_on(self) -> bool | None:
        """Return the state of the switch."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        LOGGER.info("%s: Sleep mode turned on", getattr(
            self.auto_area.area, 'name', 'unknown'))
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off switch."""
        LOGGER.info("%s: Sleep mode turned off", getattr(
            self.auto_area.area, 'name', 'unknown'))
        self._is_on = False
        self.schedule_update_ha_state()
