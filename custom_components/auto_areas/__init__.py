"""🤖 Auto Areas. A custom component for Home Assistant which automates your areas."""
from __future__ import annotations

from homeassistant.helpers import issue_registry
from homeassistant.config_entries import ConfigEntry, ConfigType
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .auto_area import (
    AutoArea,
)

from .const import DOMAIN, LOGGER, ISSUE_TYPE_YAML_DETECTED

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    # Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize AutoArea for this config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = AutoArea(hass=hass, entry=entry)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

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
