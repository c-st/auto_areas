"""
AutoLights
Toggle lights in an area based on presence.
"""
import logging
from typing import Set

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN
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
    CONFIG_PRESENCE_SCENE,
    CONFIG_GOODBYE_SCENE,
    CONFIG_SLEEPING_SCENE,
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

        self.presence_scene_entity_id = self.area_config.get(CONFIG_PRESENCE_SCENE)
        self.goodbye_scene_entity_id = self.area_config.get(CONFIG_GOODBYE_SCENE)
        self.sleeping_scene_entity_id = self.area_config.get(CONFIG_SLEEPING_SCENE)

# Auto discovery of scenes ... decided EXPLICIT scene setting is better for V1
#        self.presence_scene_entity_id = f"scene.{self.area_name}_presence"
#        self.goodbye_scene_entity_id = f"scene.{self.area_name}_goodbye"
#        for entity in all_entities:
#            if not entity.domain in SCENE_DOMAIN:
#                continue
#            if 'Presence' in entity.name:
#                self.presence_scene_entity_id = ''

        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize()
            )

    async def initialize(self) -> None:
        if self.is_sleeping_area:
            _LOGGER.info(
                "Sleeping area '%s' (entity: %s)",
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

        if initial_state == STATE_ON:
            await self.handle_presence_state_on()
        elif initial_state == STATE_OFF:
            await self.handle_presence_state_off()

        # start tracking presence state
        async_track_state_change(
            self.hass,
            self.presence_entity_id,
            self.handle_presence_state_change,
        )

    async def handle_presence_state_on(self):
        if self.sleep_mode_enabled:
            _LOGGER.info(
                "Presence detected, but sleep mode is on (%s). Not turning on lights", self.area_name
            )
            if self.sleeping_scene_entity_id:
                _LOGGER.info(
                    "Activating sleep scene (%s) %s", self.area_name, self.sleeping_scene_entity_id
                )
                await self.hass.services.async_call(
                    SCENE_DOMAIN,
                    SERVICE_TURN_ON,
                    { ATTR_ENTITY_ID: self.sleeping_scene_entity_id },
                )
            return

        # if a scene is configured, it takes precedence over the default lights on
        if self.presence_scene_entity_id:
            _LOGGER.info(
                "Activating presence scene (%s) %s", self.area_name, self.presence_scene_entity_id
            )
            await self.hass.services.async_call(
                SCENE_DOMAIN,
                SERVICE_TURN_ON,
                { ATTR_ENTITY_ID: self.presence_scene_entity_id },
            )
            return

        # if any lights, turn them on
        if self.light_entity_ids:
            _LOGGER.info(
                "Turning lights on (%s) %s", self.area_name, self.light_entity_ids
            )
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                { ATTR_ENTITY_ID: self.light_entity_ids },
            )

    async def handle_presence_state_off(self):
        # if a scene is configured, it takes precedence over the default lights off
        if self.goodbye_scene_entity_id:
            _LOGGER.info(
                "Activating goodbye scene (%s) %s", self.area_name, self.goodbye_scene_entity_id
            )            
            await self.hass.services.async_call(
                SCENE_DOMAIN,
                SERVICE_TURN_ON,
                { ATTR_ENTITY_ID: self.goodbye_scene_entity_id },
            )
            return

        # if any lights, turn them off
        if self.light_entity_ids:
            _LOGGER.info(
                "Turning lights off (%s) %s", self.area_name, self.light_entity_ids
            )            
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                { ATTR_ENTITY_ID: self.light_entity_ids },
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
            await self.handle_presence_state_on()
        else:
            await self.handle_presence_state_off()

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
            await self.handle_presence_state_off()
            
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
                await self.handle_presence_state_on()
