"""
AutoLights
Toggle lights in an area based on presence.
"""
import logging
from typing import Set

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    EVENT_HOMEASSISTANT_STARTED,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.helpers.event import async_track_state_change
from homeassistant.util import slugify

from custom_components.auto_areas.const import (
    CONFIG_SLEEPING_AREA,
    ENTITY_NAME_AREA_PRESENCE,
    ENTITY_NAME_AREA_SLEEP_MODE,
)

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
        self.area_name = slugify(area.name)
        self.area_config = area_config
        self.is_sleeping_area = self.area_config.get(CONFIG_SLEEPING_AREA, False)
        self.sleep_mode_enabled = None

        self.sleep_mode_entity_id = f"{ENTITY_NAME_AREA_SLEEP_MODE}{self.area_name}"
        self.presence_entity_id = f"{ENTITY_NAME_AREA_PRESENCE}{self.area_name}"

        self.light_entities = [
            entity for entity in all_entities if entity.domain in LIGHT_DOMAIN
        ]
        self.light_entity_ids = [entity.entity_id for entity in self.light_entities]

        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize()
            )

    async def initialize(self) -> None:
        if self.is_sleeping_area:
            _LOGGER.info(
                "Sleeping area bedroom '%s' (entity: %s)",
                self.area_name,
                self.sleep_mode_entity_id,
            )

            # set initial state
            sleep_mode_state = self.hass.states.get(self.sleep_mode_entity_id)
            if sleep_mode_state:
                self.sleep_mode_enabled = sleep_mode_state.state == STATE_ON

            # start tracking state changes
            async_track_state_change(
                self.hass,
                self.sleep_mode_entity_id,
                self.handle_sleep_mode_state_change,
            )

        # set lights initially based on presence
        initial_state = self.hass.states.get(self.presence_entity_id)
        _LOGGER.info(
            "AutoLights '%s'. Initial presence: %s, %s Managed lights: %s",
            self.area_name,
            initial_state,
            self.presence_entity_id,
            self.light_entity_ids,
        )
        if initial_state and self.light_entity_ids:
            action = (
                SERVICE_TURN_ON if initial_state.state == STATE_ON else SERVICE_TURN_OFF
            )
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                action,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )

        # start tracking presence state
        async_track_state_change(
            self.hass,
            self.presence_entity_id,
            self.handle_presence_state_change,
        )

    async def handle_presence_state_change(
        self, entity_id, from_state: State, to_state: State
    ):
        previous_state = from_state.state if from_state else ""
        current_state = to_state.state

        if previous_state == current_state:
            return

        _LOGGER.info(
            "State change: presence entity (%s) %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if current_state == STATE_ON:
            if self.sleep_mode_enabled:
                _LOGGER.info(
                    "Sleep mode is on (%s). Not turning on lights", self.area_name
                )
                return

            # turn lights on
            _LOGGER.info(
                "Turning lights on (%s) %s", self.area_name, self.light_entity_ids
            )
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )
            return
        else:
            if not self.sleep_mode_enabled:
                _LOGGER.info(
                    "Turning lights off (%s) %s", self.area_name, self.light_entity_ids
                )

            # turn lights off
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )
            return

    async def handle_sleep_mode_state_change(
        self, entity_id, from_state: State, to_state: State
    ):
        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        _LOGGER.info(
            "State change: sleep mode (%s) %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if previous_state == current_state:
            return

        if current_state == STATE_ON:
            _LOGGER.info(
                "Sleep mode enabled - turning lights off (%s) %s",
                self.area_name,
                self.light_entity_ids,
            )
            self.sleep_mode_enabled = True
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )
        else:
            _LOGGER.info("Sleep mode disabled (%s)", self.area_name)
            self.sleep_mode_enabled = False
            has_presence = (
                self.hass.states.get(self.presence_entity_id).state == STATE_ON
            )
            if has_presence:
                _LOGGER.info(
                    "Turning lights on due to presence (%s) %s",
                    self.area_name,
                    self.light_entity_ids,
                )
                await self.hass.services.async_call(
                    LIGHT_DOMAIN,
                    SERVICE_TURN_ON,
                    {ATTR_ENTITY_ID: self.light_entity_ids},
                )
