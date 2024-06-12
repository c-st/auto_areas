"""Binary sensor platform for auto_areas."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify
from homeassistant.core import Event


from .ha_helpers import all_states_are_off


from .const import (
    DOMAIN,
    NAME,
    PRESENCE_LOCK_SWITCH_ENTITY_PREFIX,
    VERSION,
    LOGGER,
    PRESENCE_BINARY_SENSOR_PREFIX,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_ON_STATES,
)

from .auto_area import AutoArea


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the binary_sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PresenceBinarySensor(auto_area)])


class PresenceBinarySensor(BinarySensorEntity):
    """Set up aggregated presence binary sensor."""

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize presence lock switch."""
        self.auto_area = auto_area
        self.presence: bool = None
        self.presence_entities: list[str] = self.get_presence_entities()
        self.unsubscribe = None
        LOGGER.info("%s: Initialized presence binary sensor",
                    self.auto_area.area.name)

    @property
    def name(self):
        """Name."""
        return f"{PRESENCE_BINARY_SENSOR_PREFIX}{self.auto_area.area.name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.config_entry.entry_id}_aggregated_presence"

    @property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return {
            "identifiers": {(DOMAIN, self.auto_area.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "suggested_area": self.auto_area.area.name,
        }

    @property
    def device_class(self):
        """Return device class."""
        return BinarySensorDeviceClass.OCCUPANCY

    @property
    def is_on(self) -> bool:
        """Return the presence state."""
        return self.presence

    def get_presence_entities(self) -> list(str):
        """Collect entities to be used for determining presence."""
        entity_ids = [
            f"{PRESENCE_LOCK_SWITCH_ENTITY_PREFIX}{
                slugify(self.auto_area.area.name)}"
        ]

        # include relevant presence entities, but not this sensor:
        for entity in self.auto_area.get_valid_entities():
            if (
                entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
                or entity.original_device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
            ) and entity.platform != DOMAIN:
                entity_ids.append(entity.entity_id)

        return entity_ids

    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.debug(
            "%s: Presence detection entities %s",
            self.auto_area.area.name,
            self.presence_entities,
        )

        # Set initial presence
        self.presence = not all_states_are_off(
            self.hass,
            self.presence_entities,
            PRESENCE_ON_STATES,
        )
        self.schedule_update_ha_state()

        LOGGER.info("%s: Initial presence %s",
                    self.auto_area.area.name, self.presence)

        # Subscribe to state changes
        self.unsubscribe = async_track_state_change_event(
            self.hass,
            self.presence_entities,
            self.handle_presence_state_change,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up event listeners."""
        if self.unsubscribe:
            self.unsubscribe()

    def handle_presence_state_change(self, event: Event):
        """Handle state change of any tracked presence sensors."""
        entity_id = event.data.get('entity_id')
        from_state = event.data.get('old_state')
        to_state = event.data.get('new_state')

        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        if previous_state == current_state:
            return

        LOGGER.debug(
            "%s: State change %s: %s -> %s",
            self.auto_area.area.name,
            entity_id,
            previous_state,
            current_state,
        )

        if current_state in PRESENCE_ON_STATES:
            if not self.presence:
                LOGGER.info("%s: Presence detected", self.auto_area.area.name)
                self.presence = True
                self.schedule_update_ha_state()
        else:
            if all_states_are_off(
                self.hass,
                self.presence_entities,
                PRESENCE_ON_STATES,
            ):
                if self.presence:
                    LOGGER.info("%s: Presence cleared",
                                self.auto_area.area.name)
                    self.presence = False
                    self.schedule_update_ha_state()
