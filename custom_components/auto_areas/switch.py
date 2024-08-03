"""Switch platform for integration_blueprint."""
from __future__ import annotations

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.auto_areas.const import CONFIG_IS_SLEEPING_AREA, DOMAIN
from custom_components.auto_areas.switches.presence_lock import PresenceLockSwitch
from custom_components.auto_areas.switches.sleep_mode import SleepModeSwitch

from .auto_area import AutoArea


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the switch platform."""
    auto_area: AutoArea = hass.data[DOMAIN][entry.entry_id]

    switch_entities: list[Entity] = [PresenceLockSwitch(auto_area)]

    if auto_area.config_entry.options.get(CONFIG_IS_SLEEPING_AREA):
        switch_entities.append(SleepModeSwitch(auto_area))

    async_add_entities(switch_entities)
