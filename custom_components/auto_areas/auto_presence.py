"""
AutoPresence
Presence based on aggregated sensors in
"""
import logging
from typing import List, Set

from homeassistant.core import HomeAssistant, State
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.helpers.event import async_track_state_change

from custom_components.auto_areas.const import (
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_BINARY_SENSOR_STATES,
)

_LOGGER = logging.getLogger(__name__)


class AutoPresence(object):
    def __init__(
        self, hass: HomeAssistant, all_entities: Set[RegistryEntry], area: AreaEntry
    ) -> None:
        self.hass = hass
        self.area = area
        self.all_entities = all_entities
        self.presence: bool = False
        self.presence_indicating_entities = []

        # Schedule initialization
        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize()
            )
        return

    async def initialize(self) -> None:
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
            if all_states_are_off(self.hass, self.presence_indicating_entities)
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
        else:
            if all_states_are_off(self.hass, self.presence_indicating_entities):
                if self.presence:
                    _LOGGER.info("Presence cleared in %s", self.area.name)
                    self.presence = False


def all_states_are_off(
    hass: HomeAssistant,
    presence_indicating_entities: List[RegistryEntry],
) -> bool:
    all_states = [
        hass.states.get(entity.entity_id) for entity in presence_indicating_entities
    ]
    return all(
        state.state not in PRESENCE_BINARY_SENSOR_STATES
        for state in filter(None, all_states)
    )
