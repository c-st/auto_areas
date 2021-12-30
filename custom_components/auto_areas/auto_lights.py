"""
AutoLights
Toggle lights in an area based on presence.
"""
import logging
from typing import Set

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.helpers.event import async_track_state_change

from custom_components.auto_areas.const import CONFIG_SLEEPING_AREA


_LOGGER = logging.getLogger(__name__)


class AutoLights(object):
    def __init__(
        self,
        hass: HomeAssistant,
        all_entities: Set[RegistryEntry],
        area: AreaEntry,
        area_config: dict,
    ) -> None:
        self.hass = hass
        self.area = area
        self.area_name = area.normalized_name
        self.area_config = area_config
        self.sleep_mode_enabled = False

        self.light_entities = [
            entity for entity in all_entities if entity.domain in LIGHT_DOMAIN
        ]

        self.initialize()

    def initialize(self) -> None:
        _LOGGER.info("AutoLights '%s'", self.area_name)

        if self.area_config.get(CONFIG_SLEEPING_AREA):
            sleep_mode_entity_id = f"switch.auto_sleep_mode_{self.area_name}"
            sleep_mode_state = self.hass.states.get(sleep_mode_entity_id)

            # handle initial state
            self.handle_sleep_mode_state_change(
                sleep_mode_entity_id, None, sleep_mode_state
            )

            # start tracking state changes
            async_track_state_change(
                self.hass,
                sleep_mode_entity_id,
                self.handle_sleep_mode_state_change,
            )

        # start tracking presence state
        async_track_state_change(
            self.hass,
            f"binary_sensor.auto_presence_{self.area_name}",
            self.handle_presence_state_change,
        )

    async def handle_presence_state_change(
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

        light_entity_ids = [entity.entity_id for entity in self.light_entities]
        _LOGGER.info(
            "Toggling light entities %s - sleep mode %s",
            light_entity_ids,
            self.sleep_mode_enabled,
        )

        if current_state == STATE_ON:
            if self.sleep_mode_enabled:
                _LOGGER.info("Sleep mode is on. Not turning on lights")
                return

            # turn lights on
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: light_entity_ids},
            )
            return
        else:
            # turn lights off
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: light_entity_ids},
            )
            return

    def handle_sleep_mode_state_change(
        self, entity_id, from_state: State, to_state: State
    ):
        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        if previous_state is current_state:
            return

        self.sleep_mode_enabled = current_state == STATE_ON
