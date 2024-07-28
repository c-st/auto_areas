"""Adds config flow for Blueprint."""

from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.helpers.area_registry import AreaRegistry, AreaEntry
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)

import homeassistant.helpers.selector as selector
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.data_entry_flow import FlowResult

from custom_components.auto_areas.calculations import (
    CALCULATE_LAST,
    CALCULATE_MAX,
    CALCULATE_MEAN,
    CALCULATE_MEDIAN,
    CALCULATE_MIN,
)

from .ha_helpers import get_all_entities

from .auto_area import AutoAreasError, AutoArea

from .const import (
    CONFIG_AREA,
    CONFIG_HUMIDITY_CALCULATION,
    CONFIG_ILLUMINANCE_CALCULATION,
    CONFIG_IS_SLEEPING_AREA,
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
    CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
    CONFIG_TEMPERATURE_CALCULATION,
    DOMAIN,
    LOGGER,
)

from .calculations import (
    DEFAULT_CALCULATION_ILLUMINANCE,
    DEFAULT_CALCULATION_TEMPERATURE,
    DEFAULT_CALCULATION_HUMIDITY,
)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_init(user_input)

    async def async_step_init(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        if user_input is not None:
            selected_area = user_input[CONFIG_AREA]
            try:
                area = self.validate_area(selected_area)
            except AutoAreasError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "area_already_managed"
            else:
                return self.async_create_entry(
                    title=area.name,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    # Areas need to have at least one entity/device before they can be selected !
                    vol.Required(
                        CONFIG_AREA,
                        default=(user_input or {}).get(
                            CONFIG_AREA),  # type: ignore
                    ): selector.AreaSelector(
                        selector.AreaSelectorConfig(
                            entity=[
                                selector.EntityFilterSelectorConfig(
                                    device_class=SensorDeviceClass.TEMPERATURE
                                ),
                                selector.EntityFilterSelectorConfig(
                                    device_class=SensorDeviceClass.HUMIDITY
                                ),
                                selector.EntityFilterSelectorConfig(
                                    device_class=SensorDeviceClass.ILLUMINANCE
                                ),
                                selector.EntityFilterSelectorConfig(
                                    device_class=BinarySensorDeviceClass.MOTION
                                ),
                                selector.EntityFilterSelectorConfig(
                                    device_class=BinarySensorDeviceClass.OCCUPANCY
                                ),
                                selector.EntityFilterSelectorConfig(
                                    device_class=BinarySensorDeviceClass.PRESENCE
                                ),
                            ],
                            multiple=False,
                        )
                    ),
                }
            ),
            errors=_errors,
        )

    def validate_area(self, area_id: str) -> AreaEntry:
        """Validate a new area to be added."""
        area_registry: AreaRegistry = ar.async_get(self.hass)
        area = area_registry.async_get_area(area_id)
        existing_configs: dict[str, AutoArea] = self.hass.data.get(DOMAIN) or {
        }
        for auto_area in existing_configs.values():
            existing_area_id = auto_area.config_entry.data.get("area")
            if existing_area_id == area_id:
                raise AutoAreasError("This area is already managed")

        return area  # type: ignore

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Show configuration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry: config_entries.ConfigEntry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONFIG_IS_SLEEPING_AREA,
                        default=(self.config_entry.options or {}).get(
                            CONFIG_IS_SLEEPING_AREA
                        )
                        or False,  # type: ignore
                    ): bool,
                    vol.Optional(
                        CONFIG_EXCLUDED_LIGHT_ENTITIES,
                        default=(self.config_entry.options or {}).get(
                            CONFIG_EXCLUDED_LIGHT_ENTITIES
                        )
                        or [],  # type: ignore
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=self.get_light_entities(),
                            exclude_entities=[],
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
                        default=(self.config_entry.options or {}).get(
                            CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE, 0
                        )
                        or 0,  # type: ignore
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=1000,
                            unit_of_measurement="lx",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONFIG_ILLUMINANCE_CALCULATION,
                        default=DEFAULT_CALCULATION_ILLUMINANCE,  # type: ignore
                    ): self.sensor_selector,
                    vol.Required(
                        CONFIG_TEMPERATURE_CALCULATION,
                        default=DEFAULT_CALCULATION_TEMPERATURE,  # type: ignore
                    ): self.sensor_selector,
                    vol.Required(
                        CONFIG_HUMIDITY_CALCULATION,
                        default=DEFAULT_CALCULATION_HUMIDITY,  # type: ignore
                    ): self.sensor_selector,
                }
            ),
        )

    def get_light_entities(self) -> list[str]:
        """Return a list of selectable light entities."""
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)
        area_id = self.config_entry.data.get(CONFIG_AREA)
        if area_id is None:
            raise ValueError(f"Missing {CONFIG_AREA} configruation value.")
        entities = [
            entity.entity_id
            for entity in get_all_entities(
                entity_registry,
                device_registry,
                area_id,
                [LIGHT_DOMAIN],
            )
        ]
        return entities

    @property
    def sensor_selector(self) -> selector.Selector:
        """Get the sensor selector configuration."""
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    CALCULATE_MEAN,
                    CALCULATE_MAX,
                    CALCULATE_MIN,
                    CALCULATE_MEDIAN,
                    CALCULATE_LAST,
                ],
                multiple=False,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
