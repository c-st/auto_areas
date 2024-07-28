"""Issue repair user flow."""
from __future__ import annotations
from typing import Any, cast

import voluptuous as vol

from homeassistant.data_entry_flow import FlowResult
from homeassistant.components.repairs import RepairsFlow
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.area_registry import (
    async_get as async_get_area_registry,
    AreaRegistry,
    AreaEntry
)
from homeassistant.helpers.issue_registry import async_delete_issue
from homeassistant.helpers.selector import (
    AreaSelector,
    AreaSelectorConfig,
    EntityFilterSelectorConfig
)
from homeassistant.core import HomeAssistant

from .const import CONFIG_AREA, LOGGER, DOMAIN
from .auto_area import AutoAreasError, AutoArea


class InvalidAreaConfigRepairFlow(RepairsFlow):
    """Handler for fixing invalid area config."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, issue_id: str) -> None:
        """Initialize repair config flow."""
        super().__init__()
        self.hass = hass
        self.entry = entry
        self.issue_id = issue_id

    async def async_step_init(
            self,
            _user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return await self.async_step_area()

    async def async_step_area(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        if user_input is not None:
            selected_area = user_input[CONFIG_AREA]
            area: AreaEntry | None = None
            try:
                area = self.validate_area(selected_area)
            except AutoAreasError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "area_already_managed"
            if area is not None:
                data = {
                    **self.entry.data,
                    CONFIG_AREA: area.id
                }
                options = {
                    **self.entry.options,
                    CONFIG_AREA: area.id
                }
                self.hass.config_entries.async_update_entry(
                    self.entry, data=data, options=options)
                await self.hass.config_entries.async_reload(self.entry.entry_id)
                async_delete_issue(self.hass, DOMAIN, self.issue_id)
                return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="area",
            data_schema=vol.Schema(
                {
                    # Areas need to have at least one entity/device before they can be selected !
                    vol.Required(
                        CONFIG_AREA, default=(user_input or {}).get(
                            CONFIG_AREA)  # type: ignore
                    ): AreaSelector(
                        AreaSelectorConfig(
                            entity=[
                                EntityFilterSelectorConfig(
                                    device_class=SensorDeviceClass.TEMPERATURE),
                                EntityFilterSelectorConfig(
                                    device_class=SensorDeviceClass.HUMIDITY),
                                EntityFilterSelectorConfig(
                                    device_class=SensorDeviceClass.ILLUMINANCE),
                                EntityFilterSelectorConfig(
                                    device_class=BinarySensorDeviceClass.MOTION),
                                EntityFilterSelectorConfig(
                                    device_class=BinarySensorDeviceClass.OCCUPANCY),
                                EntityFilterSelectorConfig(
                                    device_class=BinarySensorDeviceClass.PRESENCE),
                            ],
                            multiple=False
                        )
                    ),
                }
            ),
            errors=_errors,
        )

    def validate_area(self, area_id: str) -> AreaEntry:
        """Validate a new area to be added."""
        area_registry: AreaRegistry = async_get_area_registry(self.hass)
        area = area_registry.async_get_area(area_id)
        existing_configs: dict[str, AutoArea] = self.hass.data.get(DOMAIN) or {
        }
        if area is None:
            raise AutoAreasError("Area is not defined")
        for auto_area in existing_configs.values():
            existing_area_id = auto_area.config_entry.data.get("area")
            if existing_area_id == area_id:
                raise AutoAreasError("This area is already managed")

        return area


async def async_create_fix_flow(
        hass: HomeAssistant, issue_id: str, data: dict[str, str | int | float | None] | None
) -> RepairsFlow:
    """Create repair flow."""
    assert data
    entry_id = cast(str, data.get("entry_id", ""))
    entry = hass.config_entries.async_get_entry(entry_id)
    assert entry
    return InvalidAreaConfigRepairFlow(hass, entry, issue_id)
