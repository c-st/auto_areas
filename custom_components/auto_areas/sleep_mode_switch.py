import logging

from homeassistant.components.switch import DEVICE_CLASS_SWITCH, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaEntry

_LOGGER = logging.getLogger(__name__)


class SleepModeSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, area: AreaEntry) -> None:
        self.hass = hass
        self.area = area
        self.area_name = area.area_name
        self._is_on = False
        _LOGGER.info("Sleep Mode switch for %s", self.area_name)

    @property
    def name(self):
        return f"Auto Sleep Mode {self.area_name}"

    @property
    def device_class(self):
        return DEVICE_CLASS_SWITCH

    @property
    def is_on(self):
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        self._is_on = True

    def turn_off(self, **kwargs):
        self._is_on = False
