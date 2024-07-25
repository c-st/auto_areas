"""Base auto-entity class."""

from functools import cached_property
from typing import Generic, TypeVar, override

from homeassistant.core import Event, EventStateChangedData, State, HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import StateType
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.event import async_track_state_change_event

from .auto_area import AutoArea
from .const import DOMAIN, LOGGER, NAME, VERSION

_TDeviceClass = TypeVar(
    "_TDeviceClass", BinarySensorDeviceClass, SensorDeviceClass)
_TEntity = TypeVar("_TEntity", bound=Entity)


class AutoEntity(Entity, Generic[_TEntity, _TDeviceClass]):
    """Set up an aggregated entity."""

    def __init__(self,
                 hass: HomeAssistant,
                 auto_area: AutoArea,
                 device_class: _TDeviceClass,
                 device_classes: tuple[_TDeviceClass, ...],
                 prefix: str,
                 aggregate_type: str,
                 logger_name: str) -> None:
        """Initialize sensor."""
        super().__init__()
        self.auto_area = auto_area
        self.entities: list[str] = self.auto_area.get_valid_entity_ids(
            device_classes) or []
        self.unsubscribe = None
        self.entity_states: dict[str, State] = {}
        self._hass = hass
        self._attr_device_class = device_class
        self._device_class = device_class
        self._device_classes = device_classes
        self._prefix = prefix
        self._aggregate_type = aggregate_type
        self._logger_name = logger_name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": self.auto_area.area.name if self.auto_area.area is not None else "unknown",
        }
        self._attr_name = f"{self._prefix}{
            self.auto_area.area.name if self.auto_area.area is not None else "unknown"}"
        self._attr_unique_id = f"{
            self.auto_area.config_entry.entry_id}_aggregated_{self._aggregate_type}"
        self._attr_device_class = device_class
        LOGGER.info("%s: Initialized %s sensor", self._logger_name,
                    self.auto_area.area.name if self.auto_area.area is not None else "unknown")

    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.debug(
            "%s: %s sensor entities: %s",
            self._logger_name,
            self.auto_area.area.name if self.auto_area.area is not None else "unknown",
            self.entities,
        )

        self._attr_state = self._get_state()

        LOGGER.debug(
            "%s: initial %s: %s %s",
            self.auto_area.area.name if self.auto_area.area is not None else "unknown",
            self._logger_name or "unknown",
            getattr(self, '_attr_state', "unknown"),
            getattr(self, '_attr_unit_of_measurement', "unknown")
        )

        # Subscribe to state changes
        self.unsubscribe = async_track_state_change_event(
            self._hass,
            self.entities,
            self._handle_state_change,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up event listeners."""
        if self.unsubscribe:
            self.unsubscribe()

    def _get_state(self) -> StateType | None:
        """Get the state of the sensor."""
        calculate_state = self.auto_area.get_calculation(self._device_class)
        if calculate_state is None:
            return None
        return calculate_state(list(self.entity_states.values()))

    async def _handle_state_change(self, event: Event[EventStateChangedData]):
        """Handle state change of any tracked illuminance sensors."""
        to_state = event.data.get("new_state")
        if to_state is None:
            return

        if to_state.state in [
            "unknown",
            "unavailable",
        ]:
            self.entity_states.pop(to_state.entity_id, None)
        else:
            self.entity_states[to_state.entity_id] = to_state

        self._attr_state = self._get_state()

        self.async_schedule_update_ha_state()
