"""Auto lights."""
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import (
    STATE_ON,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    ATTR_ENTITY_ID,
)
from homeassistant.util import slugify
from homeassistant.core import Event

from .ha_helpers import get_all_entities

from .const import (
    CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
    ILLUMINANCE_SENSOR_ENTITY_PREFIX,
    LOGGER,
    CONFIG_IS_SLEEPING_AREA,
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
    PRESENCE_BINARY_SENSOR_ENTITY_PREFIX,
    SLEEP_MODE_SWITCH_ENTITY_PREFIX,
)


class AutoLights:
    """Automatic light control."""

    def __init__(self, auto_area) -> None:
        """Initialize entities."""
        self.auto_area = auto_area
        self.hass = auto_area.hass

        self.unsubscribe_sleep_mode = None
        self.unsubscribe_presence = None
        self.unsubscribe_illuminance = None

        # Config
        self.illuminance_threshold = (
            self.auto_area.config_entry.options.get(
                CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE)
            or 0
        )
        self.is_sleeping_area = (
            self.auto_area.config_entry.options.get(
                CONFIG_IS_SLEEPING_AREA) or False
        )
        self.excluded_light_entities = (
            self.auto_area.config_entry.options.get(
                CONFIG_EXCLUDED_LIGHT_ENTITIES)
            or []
        )

        self.sleep_mode_entity_id = (
            f"{SLEEP_MODE_SWITCH_ENTITY_PREFIX}{
                slugify(self.auto_area.area.name)}"
        )
        self.presence_entity_id = (
            f"{PRESENCE_BINARY_SENSOR_ENTITY_PREFIX}{
                slugify(self.auto_area.area.name)}"
        )
        self.illuminance_entity_id = (
            f"{ILLUMINANCE_SENSOR_ENTITY_PREFIX}{
                slugify(self.auto_area.area.name)}"
        )

        self.light_entity_ids = [
            entity.entity_id
            for entity in get_all_entities(
                self.auto_area.entity_registry,
                self.auto_area.device_registry,
                self.auto_area.area_id,
                [LIGHT_DOMAIN],
            )
            if entity.entity_id not in self.excluded_light_entities
        ]

        self.sleep_mode_enabled = None
        self.lights_turned_on = None

        LOGGER.debug(
            "%s: Managing light entities: %s",
            self.auto_area.area.name,
            self.light_entity_ids,
        )
        if len(self.light_entity_ids) == 0:
            LOGGER.warning(
                "%s: No light entities found to manage", self.auto_area.area.name
            )
            return

    async def initialize(self):
        """Start subscribing to state changes."""

        if self.is_sleeping_area:
            # set initial state
            sleep_mode_state = self.hass.states.get(self.sleep_mode_entity_id)
            if sleep_mode_state:
                self.sleep_mode_enabled = sleep_mode_state.state == STATE_ON
            self.unsubscribe_sleep_mode = async_track_state_change_event(
                self.hass,
                self.sleep_mode_entity_id,
                self.handle_sleep_mode_state_change,
            )

        # set lights initially based on presence
        initial_presence_state = self.hass.states.get(self.presence_entity_id)
        if initial_presence_state and self.light_entity_ids:
            if initial_presence_state.state == STATE_ON:
                await self.auto_area.hass.services.async_call(
                    LIGHT_DOMAIN,
                    SERVICE_TURN_ON,
                    {ATTR_ENTITY_ID: self.light_entity_ids},
                )
                self.lights_turned_on = True
            else:
                await self.auto_area.hass.services.async_call(
                    LIGHT_DOMAIN,
                    SERVICE_TURN_OFF,
                    {ATTR_ENTITY_ID: self.light_entity_ids},
                )
                self.lights_turned_on = False

        self.unsubscribe_presence = async_track_state_change_event(
            self.auto_area.hass,
            self.presence_entity_id,
            self.handle_presence_state_change,
        )

        self.unsubscribe_illuminance = async_track_state_change_event(
            self.auto_area.hass,
            self.illuminance_entity_id,
            self.handle_illuminance_change,
        )

    async def handle_presence_state_change(self, event: Event):
        """Handle changes in presence."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        previous_state = from_state.state if from_state else ""
        current_state = to_state.state

        LOGGER.debug(
            "%s: State change of presence entity %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if previous_state == current_state:
            return

        if current_state == STATE_ON:
            if self.sleep_mode_enabled:
                LOGGER.info(
                    "%s: Sleep mode is on. Not turning on lights",
                    self.auto_area.area.name,
                )
                return

            if self.illuminance_threshold > 0:
                current_illuminance = self.get_current_illuminance()
                if (
                    current_illuminance is not None
                    and current_illuminance > self.illuminance_threshold
                ):
                    LOGGER.info(
                        "%s: illuminance (%s lx) > threshold (%s lx). Not turning on lights",
                        self.auto_area.area.name,
                        current_illuminance,
                        self.illuminance_threshold,
                    )
                    return

            # turn lights on
            LOGGER.info(
                "%s: Turning lights on %s",
                self.auto_area.area.name,
                self.light_entity_ids,
            )
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )
            self.lights_turned_on = True
            return
        else:
            # turn lights off
            if not self.sleep_mode_enabled:
                LOGGER.info(
                    "%s: Turning lights off %s",
                    self.auto_area.area.name,
                    self.light_entity_ids,
                )
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )
            self.lights_turned_on = False

    async def handle_sleep_mode_state_change(self, event: Event):
        """Handle changes in sleep mode."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        LOGGER.debug(
            "%s: State change of sleep mode %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if previous_state == current_state:
            return

        if current_state == STATE_ON:
            LOGGER.info(
                "%s: Sleep mode enabled - turning lights off %s",
                self.auto_area.area.name,
                self.light_entity_ids,
            )
            self.sleep_mode_enabled = True
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: self.light_entity_ids},
            )
            self.lights_turned_on = False
        else:
            LOGGER.info("%s: Sleep mode disabled", self.auto_area.area.name)
            self.sleep_mode_enabled = False
            has_presence = (
                self.hass.states.get(self.presence_entity_id).state == STATE_ON
            )
            if has_presence:
                if not self.is_below_illuminance_threshold():
                    return
                LOGGER.info(
                    "%s: Turning lights on due to presence %s",
                    self.auto_area.area.name,
                    self.light_entity_ids,
                )
                await self.hass.services.async_call(
                    LIGHT_DOMAIN,
                    SERVICE_TURN_ON,
                    {ATTR_ENTITY_ID: self.light_entity_ids},
                )
                self.lights_turned_on = True

    async def handle_illuminance_change(self, _event: Event):
        """Handle changes in illuminance."""

        # Check for presence
        if self.hass.states.get(self.presence_entity_id).state != STATE_ON:
            return

        # Check for sleep mode
        if self.sleep_mode_enabled:
            return

        # Check if lights were already turned on before
        if self.lights_turned_on:
            LOGGER.debug(
                "%s: Lights were already turned on. Not turning on lights",
                self.auto_area.area.name,
            )
            return

        # Evaluate current illuminance
        if not self.is_below_illuminance_threshold():
            return

        LOGGER.info(
            "%s: Turning lights on due to illuminance %s",
            self.auto_area.area.name,
            self.light_entity_ids,
        )
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.light_entity_ids},
        )

    def is_below_illuminance_threshold(self) -> bool:
        """Evaluate if current illuminance is below threshold."""
        current_illuminance = self.get_current_illuminance()
        if self.illuminance_threshold > 0 and current_illuminance is not None:
            if current_illuminance > self.illuminance_threshold:
                LOGGER.debug(
                    "%s: illuminance (%s lx) > threshold (%s lx). Not turning on lights",
                    self.auto_area.area.name,
                    current_illuminance,
                    self.illuminance_threshold,
                )
                return False

        return True

    def get_current_illuminance(self) -> float | None:
        """Return current area illuminance."""
        try:
            current_illuminance = float(
                self.hass.states.get(self.illuminance_entity_id).state
            )
        except ValueError:
            current_illuminance = None

        return current_illuminance

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug("%s: Disabling light control", self.auto_area.area.name)
        if self.unsubscribe_sleep_mode is not None:
            self.unsubscribe_sleep_mode()

        if self.unsubscribe_presence is not None:
            self.unsubscribe_presence()

        if self.unsubscribe_illuminance is not None:
            self.unsubscribe_illuminance()
