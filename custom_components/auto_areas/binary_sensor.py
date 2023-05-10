"""Binary sensor platform for integration_blueprint."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import State
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify

from .ha_helpers import all_states_are_off


from .const import (
    DOMAIN,
    NAME,
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

    should_poll = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize presence lock switch."""
        self.auto_area = auto_area
        self.presence: bool = None

        self.presence_entities: list[str] = self.get_presence_entities()

        LOGGER.info("%s: Initialized presence binary sensor", self.auto_area.area.name)

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
        entity_ids = [f"switch.area_presence_lock_{slugify(self.auto_area.area.name)}"]

        # include relevant presence entities, but not this sensor:
        for entity in self.auto_area.get_valid_entities():
            LOGGER.info("Eval %s", entity)
            if (
                entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
                or entity.original_device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
            ) and entity.platform != DOMAIN:
                entity_ids.append(entity.entity_id)

        return entity_ids

    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.info(
            "%s starting to track",
            self.auto_area.area.name,
        )

        # if len(self.presence_indicating_entity_ids) == 1:
        #     LOGGER.info(
        #         "%s: No supported sensors for presence detection found",
        #         self.auto_area.area.name,
        #     )

        LOGGER.info(
            "%s: Using these entities for presence detection: %s",
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

        LOGGER.info("%s: Initial presence %s ", self.auto_area.area.name, self.presence)

        # Subscribe to state changes
        async_track_state_change(
            self.hass,
            self.presence_entities,
            self.handle_presence_state_change,
        )

    def handle_presence_state_change(
        self, entity_id, from_state: State, to_state: State
    ):
        """Handle state change of any tracked presence sensors."""
        previous_state = from_state.state if from_state else ""
        current_state = to_state.state if to_state else ""

        if previous_state == current_state:
            return

        LOGGER.info(
            "State change %s: %s -> %s",
            entity_id,
            previous_state,
            current_state,
        )

        if current_state in PRESENCE_ON_STATES:
            if not self.presence:
                LOGGER.info("Presence detected (%s)", self.auto_area.area.name)
                self.presence = True
                self.schedule_update_ha_state()
        else:
            if all_states_are_off(
                self.hass,
                self.presence_entities,
                PRESENCE_ON_STATES,
            ):
                if self.presence:
                    LOGGER.info("Presence cleared (%s)", self.auto_area.area.name)
                    self.presence = False
                    self.schedule_update_ha_state()
