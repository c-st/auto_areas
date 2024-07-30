"""Presence binary sensor."""

from __future__ import annotations

from functools import cached_property
from typing import Literal, override
from homeassistant.core import Event, EventStateChangedData
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.event import async_track_state_change_event

from custom_components.auto_areas.ha_helpers import all_states_are_off
from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.auto_entity import AutoEntity
from custom_components.auto_areas.const import (
    DOMAIN,
    LOGGER,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_BINARY_SENSOR_ENTITY_PREFIX,
    PRESENCE_BINARY_SENSOR_PREFIX,
    PRESENCE_LOCK_SWITCH_ENTITY_PREFIX,
    PRESENCE_ON_STATES
)


class PresenceBinarySensor(
    AutoEntity[BinarySensorEntity, BinarySensorDeviceClass], BinarySensorEntity
):
    """Set up aggregated presence binary sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize presence binary sensor."""
        super().__init__(
            hass,
            auto_area,
            BinarySensorDeviceClass.OCCUPANCY,
            PRESENCE_BINARY_SENSOR_PREFIX,
            PRESENCE_BINARY_SENSOR_ENTITY_PREFIX
        )
        self.presence: bool | None = None
        LOGGER.debug("Presence entities %s", self.entity_ids)

    @override
    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_aggregated_presence"

    @override
    @property
    def state(self) -> Literal["on", "off"] | None:  # type: ignore
        """Return the state of the binary sensor."""
        if self.presence is None:
            return None

        return STATE_ON if self.presence else STATE_OFF

    @override
    def _get_sensor_entities(self) -> list[str]:
        """Collect entities to be used for determining presence."""
        entity_ids = [
            f"{PRESENCE_LOCK_SWITCH_ENTITY_PREFIX}{
                self.auto_area.slugified_area_name}"
        ]

        for entity in self.auto_area.get_valid_entities():
            if (
                entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
                or entity.original_device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
            ) and entity.platform != DOMAIN:
                entity_ids.append(entity.entity_id)

        return entity_ids

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

        LOGGER.debug("presence sensor handling state change %s", to_state)

        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

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
