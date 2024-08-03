"""Auto lights."""
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import Event, EventStateChangedData
from homeassistant.const import (
    STATE_ON,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    ATTR_ENTITY_ID,
)
from homeassistant.util import slugify

from .const import (
    CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
    ILLUMINANCE_SENSOR_ENTITY_PREFIX,
    LIGHT_GROUP_ENTITY_PREFIX,
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

        # Entities
        self.sleep_mode_entity_id = (
            f"{SLEEP_MODE_SWITCH_ENTITY_PREFIX}{
                slugify(self.auto_area.area_name)}"
        )
        self.presence_entity_id = (
            f"{PRESENCE_BINARY_SENSOR_ENTITY_PREFIX}{
                slugify(self.auto_area.area_name)}"
        )
        self.illuminance_entity_id = (
            f"{ILLUMINANCE_SENSOR_ENTITY_PREFIX}{
                slugify(self.auto_area.area_name)}"
        )
        self.light_group_entity_id = (
            f"{LIGHT_GROUP_ENTITY_PREFIX}{
                slugify(self.auto_area.area_name)}"
        )

        self.sleep_mode_enabled = None
        self.lights_turned_on = None

        LOGGER.debug(
            "%s: Managing light group entity: %s",
            self.auto_area.area_name,
            self.light_group_entity_id,
        )

    async def initialize(self):
        """Start subscribing to state changes."""
        LOGGER.debug("AutoLights %s %s",
                     self.presence_entity_id,
                     self.illuminance_entity_id
                     )

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
        if initial_presence_state and self.light_group_entity_id:
            if initial_presence_state.state == STATE_ON:
                LOGGER.info(
                    "%s: Initial presence detected. Turning lights on %s",
                    self.auto_area.area_name,
                    self.light_group_entity_id,
                )
                await self._turn_lights_on()
            else:
                LOGGER.info(
                    "%s: No initial presence detected. Turning lights off %s",
                    self.auto_area.area_name,
                    self.light_group_entity_id,
                )
                await self._turn_lights_off()

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

    async def handle_presence_state_change(self, event: Event[EventStateChangedData]):
        """Handle changes in presence."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        LOGGER.debug("handle_presence_state_change")

        previous_state = from_state.state if from_state else ""
        if to_state is None:
            return

        current_state = to_state.state

        LOGGER.debug(
            "%s: State change of presence entity %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if previous_state == current_state or current_state is None:
            return

        if current_state == STATE_ON:
            if self.sleep_mode_enabled:
                LOGGER.info(
                    "%s: Sleep mode is on. Not turning on lights",
                    self.auto_area.area_name,
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
                        self.auto_area.area_name,
                        current_illuminance,
                        self.illuminance_threshold,
                    )
                    return

            # turn lights on
            LOGGER.info(
                "%s: Turning lights on %s",
                self.auto_area.area_name,
                self.light_group_entity_id,
            )
            await self._turn_lights_on()
            return
        else:
            # turn lights off
            if not self.sleep_mode_enabled:
                LOGGER.info(
                    "%s: Turning lights off %s",
                    self.auto_area.area_name,
                    self.light_group_entity_id,
                )
            await self._turn_lights_off()

    async def _turn_lights_on(self):
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.light_group_entity_id},
        )
        self.lights_turned_on = True

    async def _turn_lights_off(self):
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.light_group_entity_id},
        )
        self.lights_turned_on = False

    async def handle_sleep_mode_state_change(self, event: Event[EventStateChangedData]):
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
                self.auto_area.area_name,
                self.light_group_entity_id,
            )
            self.sleep_mode_enabled = True
            await self._turn_lights_off()
        else:
            LOGGER.info(
                "%s: Sleep mode disabled",
                self.auto_area.area_name,
            )
            self.sleep_mode_enabled = False
            has_presence = (
                self.hass.states.get(self.presence_entity_id).state == STATE_ON
            )
            if has_presence:
                if not self.is_below_illuminance_threshold():
                    return
                LOGGER.info(
                    "%s: Turning lights on due to presence %s",
                    self.auto_area.area_name,
                    self.light_group_entity_id,
                )
                await self._turn_lights_on()

    async def handle_illuminance_change(self, _event: Event[EventStateChangedData]):
        """Handle changes in illuminance."""

        # Check for presence
        if self.hass.states.get(self.presence_entity_id).state != STATE_ON:
            return

        # Check for sleep mode
        if self.sleep_mode_enabled:
            return

        # Check if lights were already turned on before
        if self.lights_turned_on:
            return

        # Evaluate current illuminance
        if not self.is_below_illuminance_threshold():
            return

        LOGGER.info(
            "%s: Turning lights on due to illuminance %s",
            self.auto_area.area_name,
            self.light_group_entity_id,
        )
        await self._turn_lights_on()

    def is_below_illuminance_threshold(self) -> bool:
        """Evaluate if current illuminance is below threshold."""
        current_illuminance = self.get_current_illuminance()
        if self.illuminance_threshold > 0 and current_illuminance is not None:
            if current_illuminance > self.illuminance_threshold:
                LOGGER.debug(
                    "%s: illuminance (%s lx) > threshold (%s lx). Not turning on lights",
                    self.auto_area.area_name,
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
        except (ValueError, AttributeError):
            current_illuminance = None

        return current_illuminance

    def cleanup(self):
        """Deinitialize this area."""
        LOGGER.debug(
            "%s: Disabling light control",
            self.auto_area.area_name,
        )
        if self.unsubscribe_sleep_mode is not None:
            self.unsubscribe_sleep_mode()

        if self.unsubscribe_presence is not None:
            self.unsubscribe_presence()

        if self.unsubscribe_illuminance is not None:
            self.unsubscribe_illuminance()
