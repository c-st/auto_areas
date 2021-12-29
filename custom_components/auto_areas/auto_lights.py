"""
AutoLights
Toggle lights in an area based on presence.
"""
import logging
from typing import Set

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.helpers.event import async_track_state_change


_LOGGER = logging.getLogger(__name__)


class AutoLights(object):
    def __init__(
        self, hass: HomeAssistant, all_entities: Set[RegistryEntry], area: AreaEntry
    ) -> None:
        self.hass = hass
        self.area = area

        self.light_entities = [
            entity for entity in all_entities if entity.domain in LIGHT_DOMAIN
        ]

        # listen for event when AutoAreas is setup?
        self.initialize()

    def initialize(self) -> None:
        _LOGGER.info("AutoLights '%s'", self.area.name)

        async_track_state_change(
            self.hass,
            f"binary_sensor.auto_presence_{self.area.name}",
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
            "Presence State change %s: %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if current_state is STATE_ON:
            # turn on lights
            return
        else:
            # turn lights off
            return
