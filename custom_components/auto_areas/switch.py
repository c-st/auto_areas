"""Switch platform for integration_blueprint."""
from __future__ import annotations

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
    SwitchEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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


ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="auto_areas",
        name="Integration Switch",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the switch platform."""
    LOGGER.info("Setting up switch platform")
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]

    switch_entities = [PresenceLockSwitch(auto_area)]

    if auto_area.config_entry.options.get(CONFIG_IS_SLEEPING_AREA):
        switch_entities.append(SleepModeSwitch(auto_area))

    # remove "restored" entity if sleep_mode is disabled

    async_add_entities(switch_entities)


class PresenceLockSwitch(SwitchEntity):
    """Set up a presence lock switch."""

    should_poll = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize presence lock switch."""
        self.auto_area = auto_area
        self._is_on: bool = False
        LOGGER.info("%s: Initialized presence lock switch", self.auto_area.area.name)

    @property
    def name(self):
        """Name."""
        return f"{PRESENCE_LOCK_SWITCH_PREFIX}{self.auto_area.area.name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_presence_lock"

    @property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": self.auto_area.area.name,
        }

    @property
    def device_class(self):
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        LOGGER.info("%s: Presence lock turned on", self.auto_area.area.name)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off switch."""
        LOGGER.info("%s: Presence lock turned off", self.auto_area.area.name)
        self._is_on = False
        self.schedule_update_ha_state()


class SleepModeSwitch(SwitchEntity):
    """Set up a sleep mode switch."""

    should_poll = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize sleep mode switch."""
        self.auto_area = auto_area
        self._is_on: bool = False
        LOGGER.info("%s: Initialized sleep mode switch", self.auto_area.area.name)

    @property
    def name(self):
        """Name."""
        return f"{SLEEP_MODE_SWITCH_PREFIX}{self.auto_area.area.name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_sleep_mode"

    @property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": self.auto_area.area.name,
        }

    @property
    def device_class(self):
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        LOGGER.info("%s: Sleep mode turned on", self.auto_area.area.name)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off switch."""
        LOGGER.info("%s: Sleep mode turned off", self.auto_area.area.name)
        self._is_on = False
        self.schedule_update_ha_state()
