"""
AutoPresence
Determine presence based on aggregated sensors in an area
"""
import logging
from typing import Set

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_OCCUPANCY,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.helpers.event import async_track_state_change
from homeassistant.util import slugify

from custom_components.auto_areas.const import (
    ENTITY_NAME_AREA_PRESENCE_LOCK,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_ON_STATES,
    ENTITY_FRIENDLY_NAME_AREA_PRESENCE,
)
from custom_components.auto_areas.ha_helpers import all_states_are_off

_LOGGER = logging.getLogger(__name__)


class PresenceBinarySensor(BinarySensorEntity):
    def __init__(
        self, hass: HomeAssistant, all_entities: Set[RegistryEntry], area: AreaEntry
    ) -> None:
        self.hass = hass
        self.all_entities = all_entities
        self.area = area
        self.area_name = slugify(area.name)
        self.presence: bool = None

        _LOGGER.info("AutoPresence '%s'", self.area_name)

        self.presence_lock_entity_id = (
            f"{ENTITY_NAME_AREA_PRESENCE_LOCK}{self.area_name}"
        )
        self.presence_indicating_entity_ids = [
            entity.entity_id
            for entity in self.all_entities
            if entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
            or entity.original_device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
        ] + [self.presence_lock_entity_id]

    async def async_added_to_hass(self):
        self.initialize()
        return

    def initialize(self) -> None:

        if len(self.presence_indicating_entity_ids) == 1:
            _LOGGER.info(
                "No supported sensors for presence detection found (%s)",
                self.area_name,
            )

        _LOGGER.info(
            "Using these entities for presence detection (%s): %s",
            self.area_name,
            self.presence_indicating_entity_ids,
        )

        # Set initial presence
        self.presence = (
            False
            if all_states_are_off(
                self.hass,
                self.presence_indicating_entity_ids,
                PRESENCE_ON_STATES,
            )
            else True
        )
        self.schedule_update_ha_state()

        _LOGGER.info("Initial presence (%s): %s ", self.area_name, self.presence)

        # Subscribe to state changes
        async_track_state_change(
            self.hass,
            self.presence_indicating_entity_ids,
            self.handle_presence_state_change,
        )

    @property
    def device_class(self):
        return DEVICE_CLASS_OCCUPANCY

    @property
    def name(self):
        return f"{ENTITY_FRIENDLY_NAME_AREA_PRESENCE}{self.area.name}"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool:
        return self.presence

    def handle_presence_state_change(
        self, entity_id, from_state: State, to_state: State
    ):
        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        if previous_state == current_state:
            return

        _LOGGER.info(
            "State change %s: %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if current_state in PRESENCE_ON_STATES:
            if not self.presence:
                _LOGGER.info("Presence detected (%s)", self.area_name)
                self.presence = True
                self.schedule_update_ha_state()
        else:
            if all_states_are_off(
                self.hass,
                self.presence_indicating_entity_ids,
                PRESENCE_ON_STATES,
            ):
                if self.presence:
                    _LOGGER.info("Presence cleared (%s)", self.area_name)
                    self.presence = False
                    self.schedule_update_ha_state()

    async def async_will_remove_from_hass(self):
        return
