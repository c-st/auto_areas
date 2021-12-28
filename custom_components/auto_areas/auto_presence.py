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

from custom_components.auto_areas.const import (
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_BINARY_SENSOR_STATES,
)
from custom_components.auto_areas.ha_helpers import all_states_are_off

_LOGGER = logging.getLogger(__name__)


class AutoPresenceBinarySensor(BinarySensorEntity):
    def __init__(
        self, hass: HomeAssistant, all_entities: Set[RegistryEntry], area: AreaEntry
    ) -> None:
        self.hass = hass
        self.area = area

        self.all_entities = all_entities
        self.presence_indicating_entities = []

        self.presence: bool = None

        self.initialize()

    @property
    def device_class(self):
        """Return the device class of the entity."""
        return DEVICE_CLASS_OCCUPANCY

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Auto Presence {self.area.name}"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool:
        return self.presence

    def initialize(self) -> None:
        """Register relevant entities from this area"""
        _LOGGER.info("AutoPresence '%s'", self.area.name)

        self.presence_indicating_entities = [
            entity
            for entity in self.all_entities
            if entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
            or entity.original_device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
        ]

        if not self.presence_indicating_entities:
            _LOGGER.info(
                "* No presence binary_sensors found in area %s",
                self.area.name,
            )
            return

        _LOGGER.info(
            "- Tracking: %s ",
            [entity.entity_id for entity in self.presence_indicating_entities],
        )

        # Initial presence:
        self.presence = (
            False
            if all_states_are_off(
                self.hass,
                self.presence_indicating_entities,
                PRESENCE_BINARY_SENSOR_STATES,
            )
            else True
        )
        _LOGGER.info("Initial presence (%s): %s ", self.area.name, self.presence)

        # Subscribe to state changes
        async_track_state_change(
            self.hass,
            [entity.entity_id for entity in self.presence_indicating_entities],
            self.handle_presence_state_change,
        )

    def handle_presence_state_change(
        self, entity_id, from_state: State, to_state: State
    ):
        previous_state = from_state.state if from_state else ""
        current_state = to_state.state

        if previous_state is current_state:
            return

        _LOGGER.info(
            "State change %s: %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        # Find entity and set its state

        if current_state in PRESENCE_BINARY_SENSOR_STATES:
            if not self.presence:
                _LOGGER.info("Presence detected in %s", self.area.name)
                self.presence = True
                self.schedule_update_ha_state()
        else:
            if all_states_are_off(
                self.hass,
                self.presence_indicating_entities,
                PRESENCE_BINARY_SENSOR_STATES,
            ):
                if self.presence:
                    _LOGGER.info("Presence cleared in %s", self.area.name)
                    self.presence = False
                    self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        _LOGGER.info("callback async_added_to_hass")

    async def async_will_remove_from_hass(self):
        _LOGGER.info("callback async_will_remove_from_hass")
