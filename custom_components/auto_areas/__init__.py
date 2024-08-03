"""🤖 Auto Areas. A custom component for Home Assistant which automates your areas."""
from __future__ import annotations
import asyncio

from homeassistant.helpers import issue_registry
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED


from .auto_area import (
    AutoArea,
)

from .const import DOMAIN, LOGGER, ISSUE_TYPE_YAML_DETECTED

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize AutoArea for this config entry."""
    hass.data.setdefault(DOMAIN, {})

    auto_area = AutoArea(hass=hass, entry=entry)
    hass.data[DOMAIN][entry.entry_id] = auto_area

    if hass.is_running:
        # Initialize immediately
        await async_init(hass, entry, auto_area)
    else:
        # Schedule initialization when HA is started and initialized
        # https://developers.home-assistant.io/docs/asyncio_working_with_async/#calling-async-functions-from-threads

        @callback
        def init(hass: HomeAssistant, entry: ConfigEntry, auto_area: AutoArea):
            asyncio.run_coroutine_threadsafe(
                async_init(hass, entry, auto_area), hass.loop
            ).result()

        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            lambda params: init(hass, entry, auto_area)
        )

    return True


async def async_init(hass: HomeAssistant, entry: ConfigEntry, auto_area: AutoArea):
    """Initialize component."""
    await asyncio.sleep(5)  # wait for all area devices to be initialized
    await auto_area.async_initialize()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    LOGGER.info("🔄 Reloading entry %s", entry)

    await hass.config_entries.async_reload(entry.entry_id)


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
