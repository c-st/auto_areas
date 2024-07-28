"""Binary sensor platform for auto_areas."""

from __future__ import annotations

from functools import cached_property
from typing import Literal, override
from homeassistant.core import Event, EventStateChangedData
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from custom_components.auto_areas.ha_helpers import all_states_are_off

from .auto_entity import AutoEntity

from .auto_area import AutoArea
from .const import (
    DOMAIN,
    LOGGER,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_BINARY_SENSOR_ENTITY_PREFIX,
    PRESENCE_BINARY_SENSOR_PREFIX,
    PRESENCE_ON_STATES,
)


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the binary_sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PresenceBinarySensor(hass, auto_area)])


class PresenceBinarySensor(
    AutoEntity[BinarySensorEntity, BinarySensorDeviceClass], BinarySensorEntity
):
    """Set up aggregated presence binary sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize presence binary sensor."""
        super().__init__(
            hass,
            auto_area,
            BinarySensorDeviceClass.PRESENCE,
            PRESENCE_BINARY_SENSOR_PREFIX,
            PRESENCE_BINARY_SENSOR_ENTITY_PREFIX
        )
        self.presence: bool | None = None
        LOGGER.debug("Presence entities %s", self.entity_ids)

    @cached_property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.presence

    @cached_property
    def state(self) -> Literal["on", "off"] | None:  # type: ignore
        """Return the state of the binary sensor."""
        if (is_on := self.is_on) is None:
            return None
        return STATE_ON if is_on else STATE_OFF

    @override
    def _get_sensor_entities(self) -> list[str]:
        """Retrieve all relevant presence entities."""
        return [
            entity.entity_id
            for entity in self.auto_area.get_valid_entities()
            if entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
            or entity.original_device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
        ]

    @override
    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.debug(
            "%s: Presence detection entities %s",
            self.auto_area.area_name,
            self.entity_ids,
        )

        # Set initial presence
        self.presence = not all_states_are_off(
            self.hass,
            self.entity_ids,
            PRESENCE_ON_STATES,
        )
        self.schedule_update_ha_state()

        LOGGER.info(
            "%s: Initial presence %s",
            self.auto_area.area_name,
            self.presence
        )

        # Subscribe to state changes
        self.unsubscribe = async_track_state_change_event(
            self.hass,
            self.entity_ids,
            self._handle_state_change,
        )

    @override
    async def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        """Handle state change of any tracked presence sensors."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        LOGGER.debug("presence sensor handling state change %s", current_state)

        if previous_state == current_state:
            return

        LOGGER.debug(
            "%s: State change %s: %s -> %s",
            self.auto_area.area_name,
            entity_id,
            previous_state,
            current_state,
        )

        if current_state in PRESENCE_ON_STATES:
            if not self.presence:
                LOGGER.info("%s: Presence detected", self.auto_area.area_name)
                self.presence = True
                self.schedule_update_ha_state()
        else:
            if all_states_are_off(
                self.hass,
                self.entity_ids,
                PRESENCE_ON_STATES,
            ):
                if self.presence:
                    LOGGER.info(
                        "%s: Presence cleared",
                        self.auto_area.area_name
                    )
                    self.presence = False
                    self.schedule_update_ha_state()
