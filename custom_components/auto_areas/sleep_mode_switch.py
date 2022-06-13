import logging

from homeassistant.components.switch import DEVICE_CLASS_SWITCH, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.util import slugify

from custom_components.auto_areas.const import ENTITY_FRIENDLY_NAME_AREA_SLEEP_MODE

_LOGGER = logging.getLogger(__name__)


class SleepModeSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, area: AreaEntry) -> None:
        self.hass = hass
        self.area = area
        self.area_name = slugify(area.name)
        self._is_on: bool = False
        _LOGGER.info("Sleep Mode switch for %s", self.area_name)

    @property
    def name(self):
        return f"{ENTITY_FRIENDLY_NAME_AREA_SLEEP_MODE}{self.area.name}"

    @property
    def device_class(self):
        return DEVICE_CLASS_SWITCH

    @property
    def is_on(self):
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        _LOGGER.info("Sleep mode (%s) turned on", self.area_name)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        _LOGGER.info("Sleep mode (%s) turned off", self.area_name)
        self._is_on = False
        self.schedule_update_ha_state()

    @property
    def unique_id(self):
        return f"auto_areas_sleep_switch_{self.area_name}"
