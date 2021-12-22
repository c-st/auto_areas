"""An AutoArea"""
import logging

from typing import List, Optional, Set

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import AreaEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry
from homeassistant.helpers.device_registry import DeviceRegistry

from custom_components.auto_areas.const import (
    DOMAINS,
    PRESENCE_BINARY_SENSOR_DEVICE_CLASSES,
    PRESENCE_BINARY_SENSOR_STATES,
)

_LOGGER = logging.getLogger(__name__)


class AutoArea(object):
    """An area managed by AutoAreas"""

    def __init__(self, hass: HomeAssistant, area: AreaEntry) -> None:
        self.hass = hass
        self.area_name = area.name
        self.area_id = area.id
        self.presence: bool = False
        self.entities: Set[RegistryEntry] = set()

        # Schedule initialization of entities for this area:
        if self.hass.is_running:
            self.hass.async_create_task(self.initialize())
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.initialize
            )

    async def initialize(self) -> None:
        """Register relevant entities for this area"""
        _LOGGER.info("AutoArea %s", self.area_name)
        entity_registry: EntityRegistry = (
            await self.hass.helpers.entity_registry.async_get_registry()
        )
        device_registry: DeviceRegistry = (
            await self.hass.helpers.device_registry.async_get_registry()
        )

        # Collect entities for this area
        self.entities = get_all_entities(
            entity_registry, device_registry, self.area_id, DOMAINS
        )
        for entity in self.entities:
            _LOGGER.info(
                "- Entity %s (class: %s)", entity.entity_id, entity.device_class
            )

        # Track state of all presence/motion sensors
        self.track_presence_sensor_state()

    def track_presence_sensor_state(self) -> None:
        """Subscribes to state updates of all presence sensors"""
        presence_indicating_entities = [
            entity
            for entity in self.entities
            if entity.device_class in PRESENCE_BINARY_SENSOR_DEVICE_CLASSES
        ]

        if not presence_indicating_entities:
            _LOGGER.info("* No presence binary_sensors found for tracking")
            return

        for entity in presence_indicating_entities:
            _LOGGER.info("- Tracking: %s ", entity.entity_id)

        def handle_presence_state_change(entity_id, from_state: State, to_state: State):
            _LOGGER.info(
                "State change %s: %s -> %s",
                entity_id,
                from_state.state if from_state else "None",
                to_state.state,
            )

            if to_state.state in PRESENCE_BINARY_SENSOR_STATES:
                self.presence = True
            else:
                # check if all sensors are off
                all_states = [
                    self.hass.states.get(entity.entity_id).state
                    for entity in presence_indicating_entities
                ]
                if all(
                    state not in PRESENCE_BINARY_SENSOR_STATES for state in all_states
                ):
                    self.presence = False

        async_track_state_change(
            self.hass,
            [entity.entity_id for entity in presence_indicating_entities],
            handle_presence_state_change,
        )

        return


def get_all_entities(
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    area_id: str,
    domains: List[str] = None,
) -> List:
    """Returns all entities from an area"""
    entities = []

    for _entity_id, entity in entity_registry.entities.items():
        # _LOGGER.info("Entity %s %s", entity.domain, entity.device_class)

        if not is_valid(entity):
            continue

        if not get_area_id(entity, device_registry) == area_id:
            continue

        if entity.domain not in domains:
            continue

        entities.append(entity)

    return entities


def is_valid(entity: RegistryEntry) -> bool:
    """Checks whether an entity should be included"""
    if entity.disabled:
        return False

    return True


def get_area_id(
    entity: RegistryEntry, device_registry: DeviceRegistry
) -> Optional[str]:
    """Determines area_id from a registry entry"""
    # Check entity_id of entity:
    if entity.area_id is not None:
        return entity.area_id

    # Check area of device from device registry
    if entity.device_id is not None:
        device = device_registry.devices[entity.device_id]
        if device is not None:
            return device.area_id

    return None
