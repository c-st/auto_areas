"""Environmental safety binary sensor."""

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
    SAFETY_BINARY_SENSOR_DEVICE_CLASSES,
    SAFETY_BINARY_SENSOR_ENTITY_PREFIX,
    SAFETY_BINARY_SENSOR_PREFIX,
)


class SafetyBinarySensor(
    AutoEntity[BinarySensorEntity, BinarySensorDeviceClass], BinarySensorEntity
):
    """Set up aggregated environmental safety binary sensor."""

    def __init__(self, hass, auto_area: AutoArea) -> None:
        """Initialize safety binary sensor."""
        super().__init__(
            hass,
            auto_area,
            BinarySensorDeviceClass.SAFETY,
            SAFETY_BINARY_SENSOR_PREFIX,
            SAFETY_BINARY_SENSOR_ENTITY_PREFIX
        )
        self.safety_alert: bool | None = None
        LOGGER.debug("Safety entities %s", self.entity_ids)

    @override
    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_aggregated_safety"

    @override
    @property
    def icon(self) -> str:
        """Return icon based on safety state."""
        if self.safety_alert:
            return "mdi:shield-alert"
        return "mdi:shield-check"

    @override
    @property
    def state(self) -> Literal["on", "off"] | None:  # type: ignore
        """Return the state of the binary sensor."""
        if self.safety_alert is None:
            return None

        return STATE_ON if self.safety_alert else STATE_OFF

    @override
    def _get_sensor_entities(self) -> list[str]:
        """Collect entities to be used for determining safety alerts."""
        entity_ids: list[str] = []

        for entity in self.auto_area.get_valid_entities():
            if (
                entity.device_class in SAFETY_BINARY_SENSOR_DEVICE_CLASSES
                or entity.original_device_class in SAFETY_BINARY_SENSOR_DEVICE_CLASSES
            ) and entity.platform != DOMAIN:
                entity_ids.append(entity.entity_id)

        return entity_ids

    @override
    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.debug(
            "%s: Safety detection entities %s",
            self.auto_area.area_name,
            self.entity_ids,
        )

        # Set initial safety state
        self.safety_alert = self._any_sensor_on()
        self.async_write_ha_state()

        LOGGER.info(
            "%s: Initial safety alert %s",
            self.auto_area.area_name,
            self.safety_alert
        )

        # Subscribe to state changes
        self.unsubscribe = async_track_state_change_event(
            self.hass,
            self.entity_ids,
            self._handle_state_change,
        )

    def _any_sensor_on(self) -> bool:
        """Check if any tracked safety sensor is currently on."""
        for entity_id in self.entity_ids:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state == STATE_ON:
                return True
        return False

    @override
    async def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        """Handle state change of any tracked safety sensors."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        LOGGER.debug("safety sensor handling state change %s", to_state)

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
            new_alert = self._any_sensor_on()
            if new_alert != self.safety_alert:
                self.safety_alert = new_alert
                self.async_write_ha_state()
            return

        if current_state == STATE_ON:
            if not self.safety_alert:
                LOGGER.debug("%s: Safety alert triggered", self.auto_area.area_name)
                self.safety_alert = True
                self.async_write_ha_state()
        else:
            # A sensor turned off — check if all are now off
            if not self._any_sensor_on():
                if self.safety_alert:
                    LOGGER.debug(
                        "%s: Safety alert cleared",
                        self.auto_area.area_name
                    )
                    self.safety_alert = False
                    self.async_write_ha_state()
