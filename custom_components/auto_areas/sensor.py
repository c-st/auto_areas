"""Sensor platform for auto_areas."""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.core import State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, LOGGER, ILLUMINANCE_SENSOR_PREFIX, VERSION, NAME
from .auto_area import AutoArea


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]
    # only setup if there is at least one sensor
    async_add_entities([IlluminanceSensor(auto_area)])


class IlluminanceSensor(SensorEntity):
    """Set up aggregated illuminance sensor."""

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize sensor."""
        self.auto_area = auto_area
        self.illuminance_entities: list[str] = self.get_illuminance_entities()
        self.unsubscribe = None
        self.value = None
        LOGGER.info("%s: Initialized illuminance sensor", self.auto_area.area.name)

    @property
    def name(self):
        """Name."""
        return f"{ILLUMINANCE_SENSOR_PREFIX}{self.auto_area.area.name}"

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
    def device_class(self) -> SensorDeviceClass:
        """Return device class."""
        return SensorDeviceClass.ILLUMINANCE

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurment."""
        return "lx"

    @property
    def native_value(self):
        """Return current value."""
        return self.value

    def get_illuminance_entities(self):
        """Collect entities for determining illuminance."""
        entity_ids = []
        # include relevant entities, but not this sensor:
        for entity in self.auto_area.get_valid_entities():
            if (
                SensorDeviceClass.ILLUMINANCE
                in [entity.device_class, entity.original_device_class]
            ) and entity.platform != DOMAIN:
                entity_ids.append(entity.entity_id)

        return entity_ids

    async def async_added_to_hass(self):
        """Start tracking sensors."""
        LOGGER.debug(
            "%s: Illuminance sensor entities: %s",
            self.auto_area.area.name,
            self.illuminance_entities,
        )

        # # set initial illuminance
        for entity_id in self.illuminance_entities:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in [
                "unknown",
                "unavailable",
            ]:
                self.value = state.state

        if self.value is not None:
            LOGGER.debug(
                "%s: initial illuminance: %s lux", self.auto_area.area.name, self.value
            )

        # Subscribe to state changes
        self.unsubscribe = async_track_state_change(
            self.hass,
            self.illuminance_entities,
            self.handle_illuminance_change,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up event listeners."""
        if self.unsubscribe:
            self.unsubscribe()

    def handle_illuminance_change(
        self, _entity_id, _from_state: State, to_state: State
    ):
        """Handle state change of any tracked illuminance sensors."""
        if to_state.state not in [
            "unknown",
            "unavailable",
        ]:
            self.value = to_state.state
            self.schedule_update_ha_state()
