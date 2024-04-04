"""🤖 Auto Areas. A custom component for Home Assistant which automates your areas."""
from __future__ import annotations
import asyncio

from homeassistant.helpers import issue_registry
from homeassistant.config_entries import ConfigEntry, ConfigType
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED


from .auto_area import (
    AutoArea,
)

from .const import DOMAIN, LOGGER, ISSUE_TYPE_YAML_DETECTED

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize AutoArea for this config entry."""
    hass.data.setdefault(DOMAIN, {})

    auto_area = AutoArea(hass=hass, entry=entry)
    hass.data[DOMAIN][entry.entry_id] = auto_area

    # Initialize AutoArea once HA is started
    if hass.is_running:
        await auto_area.initialize()
    else:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            lambda init: initialize(hass, auto_area)
        )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

def initialize(hass: HomeAssistant, auto_area: AutoArea):
    """Initialize area after HA has started."""
    return asyncio.run_coroutine_threadsafe(
        auto_area.initialize(), hass.loop
    ).result()

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    # unsubscribe from changes:
    hass.data[DOMAIN][entry.entry_id].cleanup()

    # unload platforms:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        LOGGER.warning("Unloaded successfully %s", entry.entry_id)
    else:
        LOGGER.error("Couldn't unload config entry %s", entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Check for YAML-config."""

    if config.get("auto_areas") is not None:
        LOGGER.warning(
            "Detected an existing YAML configuration. "
            + "This is not supported anymore, please remove it."
        )
        issue_registry.async_create_issue(
            hass,
            DOMAIN,
            ISSUE_TYPE_YAML_DETECTED,
            is_fixable=False,
            is_persistent=False,
            severity=issue_registry.IssueSeverity.WARNING,
            translation_key=ISSUE_TYPE_YAML_DETECTED,
        )

    return True
