"""Adds config flow for Blueprint."""
from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant import helpers
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.helpers.area_registry import AreaRegistry

import homeassistant.helpers.selector as selector

from homeassistant.data_entry_flow import FlowResult

from .ha_helpers import get_all_entities

from .auto_area import AutoAreasError, AutoArea

from .const import (
    CONFIG_AREA,
    CONFIG_IS_SLEEPING_AREA,
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
    DOMAIN,
    LOGGER,
)


# get all areas:
# area_registry: AreaRegistry = helpers.area_registry.async_get(self.hass)
# all_areas = {a.id: a.name for a in area_registry.async_list_areas()}


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_init(user_input)

    # this has to be named according to async_step_<step>
    async def async_step_init(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
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
                        CONFIG_AREA, default=(user_input or {}).get(CONFIG_AREA)
                    ): selector.AreaSelector(
                        selector.AreaSelectorConfig(multiple=False)
                    ),
                }
            ),
            errors=_errors,
        )

    def validate_area(self, area_id: str):
        """Validate a new area to be added."""
        area_registry: AreaRegistry = helpers.area_registry.async_get(self.hass)
        area = area_registry.async_get_area(area_id)
        existing_configs: dict[str, AutoArea] = self.hass.data.get(DOMAIN) or {}
        for auto_area in existing_configs.values():
            existing_area_id = auto_area.config_entry.data.get("area")
            if existing_area_id == area_id:
                raise AutoAreasError("This area is already managed")

        return area

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
                        or False,
                    ): bool,
                    vol.Optional(
                        CONFIG_EXCLUDED_LIGHT_ENTITIES,
                        default=(self.config_entry.options or {}).get(
                            CONFIG_EXCLUDED_LIGHT_ENTITIES
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            include_entities=self.get_light_entities(),
                            exclude_entities=[],
                            multiple=True,
                        )
                    ),
                }
            ),
        )

    def get_light_entities(self) -> list[str]:
        """Return a list of selectable light entities."""
        device_registry = helpers.device_registry.async_get(self.hass)
        entity_registry = helpers.entity_registry.async_get(self.hass)

        entities = [
            entity.entity_id
            for entity in get_all_entities(
                entity_registry,
                device_registry,
                self.config_entry.data.get(CONFIG_AREA),
                [LIGHT_DOMAIN],
            )
        ]
        return entities
