"""Area open/closed binary sensor."""

from __future__ import annotations

from typing import Literal, override
from homeassistant.core import Event, EventStateChangedData
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.event import async_track_state_change_event

from custom_components.auto_areas.auto_area import AutoArea
from custom_components.auto_areas.auto_entity import AutoEntity
from custom_components.auto_areas.const import (
    DOMAIN,
    LOGGER,
    OPEN_BINARY_SENSOR_DEVICE_CLASSES,
    OPEN_BINARY_SENSOR_ENTITY_PREFIX,
    OPEN_BINARY_SENSOR_PREFIX,
)


class OpenBinarySensor(
    AutoEntity[BinarySensorEntity, BinarySensorDeviceClass], BinarySensorEntity
):
    """Set up aggregated open/closed binary sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize open binary sensor."""
        super().__init__(
            hass,
            auto_area,
            BinarySensorDeviceClass.OPENING,
            OPEN_BINARY_SENSOR_PREFIX,
            OPEN_BINARY_SENSOR_ENTITY_PREFIX
        )
        self.any_open: bool | None = None
        LOGGER.debug("Open entities %s", self.entity_ids)

    @override
    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_aggregated_open"

    @override
    @property
    def icon(self) -> str:
        """Return icon based on open state."""
        if self.any_open:
            return "mdi:door-open"
        return "mdi:door-closed"

    @override
    @property
    def state(self) -> Literal["on", "off"] | None:  # type: ignore
        """Return the state of the binary sensor."""
        if self.any_open is None:
            return None

        return STATE_ON if self.any_open else STATE_OFF

    @override
    def _get_sensor_entities(self) -> list[str]:
        """Collect entities to be used for determining open/closed state."""
        entity_ids: list[str] = []

        for entity in self.auto_area.get_valid_entities():
            if (
                entity.device_class in OPEN_BINARY_SENSOR_DEVICE_CLASSES
                or entity.original_device_class in OPEN_BINARY_SENSOR_DEVICE_CLASSES
            ) and entity.platform != DOMAIN:
                entity_ids.append(entity.entity_id)

        return entity_ids

    @override
    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.debug(
            "%s: Open detection entities %s",
            self.auto_area.area_name,
            self.entity_ids,
        )

        # Set initial open state
        self.any_open = self._any_sensor_on()
        self.async_write_ha_state()

        LOGGER.info(
            "%s: Initial open state %s",
            self.auto_area.area_name,
            self.any_open
        )

        # Subscribe to state changes
        self.unsubscribe = async_track_state_change_event(
            self.hass,
            self.entity_ids,
            self._handle_state_change,
        )

    def _any_sensor_on(self) -> bool:
        """Check if any tracked open/closed sensor is currently on (open)."""
        for entity_id in self.entity_ids:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state == STATE_ON:
                return True
        return False

    @override
    async def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        """Handle state change of any tracked open/closed sensors."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        LOGGER.debug("open sensor handling state change %s", to_state)

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

        # Ignore unknown/unavailable transitions — recalculate from remaining sensors
        if current_state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            new_open = self._any_sensor_on()
            if new_open != self.any_open:
                self.any_open = new_open
                self.async_write_ha_state()
            return

        if current_state == STATE_ON:
            if not self.any_open:
                LOGGER.debug("%s: Open state triggered", self.auto_area.area_name)
                self.any_open = True
                self.async_write_ha_state()
        else:
            # A sensor closed — check if all are now closed
            if not self._any_sensor_on():
                if self.any_open:
                    LOGGER.debug(
                        "%s: All closed",
                        self.auto_area.area_name
                    )
                    self.any_open = False
                    self.async_write_ha_state()
