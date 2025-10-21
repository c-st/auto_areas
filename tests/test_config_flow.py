"""Test Auto Areas config flow."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.auto_areas.config_flow import ConfigFlowHandler, OptionsFlowHandler
from custom_components.auto_areas.auto_area import AutoAreasError
from custom_components.auto_areas.const import (
    DOMAIN,
    CONFIG_AREA,
    CONFIG_IS_SLEEPING_AREA,
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
    CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE,
)


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_area_registry():
    """Create a mock area registry."""
    area_registry = MagicMock()
    mock_area = MagicMock()
    mock_area.name = "Test Room"
    mock_area.id = "test_room_id"
    area_registry.async_get_area.return_value = mock_area
    return area_registry


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=config_entries.ConfigEntry)
    entry.data = {CONFIG_AREA: "test_room_id"}
    entry.options = {
        CONFIG_IS_SLEEPING_AREA: False,
        CONFIG_EXCLUDED_LIGHT_ENTITIES: [],
        CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 100,
    }
    return entry


class TestConfigFlow:
    """Test the config flow."""

    @pytest.mark.asyncio
    async def test_async_step_user_calls_init(self):
        """Test that user step calls init step."""
        flow = ConfigFlowHandler()
        flow.async_step_init = AsyncMock()

        await flow.async_step_user(None)

        flow.async_step_init.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_async_step_init_no_input_shows_form(self):
        """Test init step shows form when no user input."""
        flow = ConfigFlowHandler()
        flow.hass = MagicMock()

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "init"
        assert CONFIG_AREA in result["data_schema"].schema

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.config_flow.ar.async_get")
    async def test_async_step_init_valid_area_creates_entry(self, mock_ar_get, mock_hass, mock_area_registry):
        """Test init step creates entry with valid area."""
        mock_ar_get.return_value = mock_area_registry

        flow = ConfigFlowHandler()
        flow.hass = mock_hass

        user_input = {CONFIG_AREA: "test_room_id"}

        result = await flow.async_step_init(user_input=user_input)

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Test Room"
        assert result["data"] == user_input

    @pytest.mark.asyncio
    @patch("custom_components.auto_areas.config_flow.ar.async_get")
    async def test_async_step_init_duplicate_area_shows_error(self, mock_ar_get, mock_hass, mock_area_registry):
        """Test init step shows error for duplicate area."""
        mock_ar_get.return_value = mock_area_registry

        # Setup existing auto area
        existing_auto_area = MagicMock()
        existing_auto_area.config_entry.data = {CONFIG_AREA: "test_room_id"}
        mock_hass.data[DOMAIN] = {"existing_entry": existing_auto_area}

        flow = ConfigFlowHandler()
        flow.hass = mock_hass

        user_input = {CONFIG_AREA: "test_room_id"}

        result = await flow.async_step_init(user_input=user_input)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"]["base"] == "area_already_managed"

    def test_validate_area_success(self, mock_hass, mock_area_registry):
        """Test area validation with valid area."""
        with patch("custom_components.auto_areas.config_flow.ar.async_get") as mock_ar_get:
            mock_ar_get.return_value = mock_area_registry

            flow = ConfigFlowHandler()
            flow.hass = mock_hass

            area = flow.validate_area("test_room_id")

            assert area is not None
            assert area.name == "Test Room"

    def test_validate_area_already_managed_raises_error(self, mock_hass, mock_area_registry):
        """Test area validation raises error for duplicate area."""
        with patch("custom_components.auto_areas.config_flow.ar.async_get") as mock_ar_get:
            mock_ar_get.return_value = mock_area_registry

            # Setup existing auto area
            existing_auto_area = MagicMock()
            existing_auto_area.config_entry.data = {CONFIG_AREA: "test_room_id"}
            mock_hass.data[DOMAIN] = {"existing_entry": existing_auto_area}

            flow = ConfigFlowHandler()
            flow.hass = mock_hass

            with pytest.raises(AutoAreasError):
                flow.validate_area("test_room_id")

    def test_validate_area_different_areas_allowed(self, mock_hass, mock_area_registry):
        """Test that different areas can be added."""
        with patch("custom_components.auto_areas.config_flow.ar.async_get") as mock_ar_get:
            mock_ar_get.return_value = mock_area_registry

            # Setup existing auto area for different room
            existing_auto_area = MagicMock()
            existing_auto_area.config_entry.data = {CONFIG_AREA: "other_room_id"}
            mock_hass.data[DOMAIN] = {"existing_entry": existing_auto_area}

            flow = ConfigFlowHandler()
            flow.hass = mock_hass

            # Should not raise error for different area
            area = flow.validate_area("test_room_id")
            assert area is not None

    def test_async_get_options_flow(self, mock_config_entry):
        """Test getting options flow."""
        options_flow = ConfigFlowHandler.async_get_options_flow(mock_config_entry)

        assert isinstance(options_flow, OptionsFlowHandler)
        assert options_flow.config_entry == mock_config_entry


class TestOptionsFlow:
    """Test the options flow."""

    def test_init(self, mock_config_entry):
        """Test options flow initialization."""
        flow = OptionsFlowHandler(mock_config_entry)

        assert flow.config_entry == mock_config_entry

    @pytest.mark.asyncio
    async def test_async_step_init_no_input_shows_form(self, mock_config_entry):
        """Test init step shows form when no user input."""
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        with patch.object(flow, 'get_light_entities', return_value=[]):
            result = await flow.async_step_init(user_input=None)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_async_step_init_creates_entry_with_input(self, mock_config_entry):
        """Test init step creates entry with user input."""
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        user_input = {
            CONFIG_IS_SLEEPING_AREA: True,
            CONFIG_EXCLUDED_LIGHT_ENTITIES: ["light.excluded"],
            CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 50,
        }

        result = await flow.async_step_init(user_input=user_input)

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_async_step_init_uses_default_values(self, mock_config_entry):
        """Test that form uses default values from config entry."""
        mock_config_entry.options = {
            CONFIG_IS_SLEEPING_AREA: True,
            CONFIG_EXCLUDED_LIGHT_ENTITIES: ["light.test"],
            CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 75,
        }

        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        with patch.object(flow, 'get_light_entities', return_value=["light.test", "light.other"]):
            result = await flow.async_step_init(user_input=None)

        assert result["type"] == data_entry_flow.FlowResultType.FORM

    @patch("custom_components.auto_areas.config_flow.er.async_get")
    @patch("custom_components.auto_areas.config_flow.dr.async_get")
    @patch("custom_components.auto_areas.config_flow.get_all_entities")
    def test_get_light_entities(self, mock_get_all_entities, mock_dr, mock_er, mock_config_entry):
        """Test getting light entities for area."""
        # Setup mock entities
        mock_entity1 = MagicMock()
        mock_entity1.entity_id = "light.test_1"
        mock_entity2 = MagicMock()
        mock_entity2.entity_id = "light.test_2"

        mock_get_all_entities.return_value = [mock_entity1, mock_entity2]

        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        entities = flow.get_light_entities()

        assert "light.test_1" in entities
        assert "light.test_2" in entities
        assert len(entities) == 2

    @patch("custom_components.auto_areas.config_flow.er.async_get")
    @patch("custom_components.auto_areas.config_flow.dr.async_get")
    def test_get_light_entities_missing_area_raises_error(self, mock_dr, mock_er):
        """Test get_light_entities raises error when area config missing."""
        mock_config_entry = MagicMock(spec=config_entries.ConfigEntry)
        mock_config_entry.data = {}  # No area configured

        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        with pytest.raises(ValueError, match="Missing area"):
            flow.get_light_entities()

    def test_sensor_selector_property(self, mock_config_entry):
        """Test sensor selector property returns correct config."""
        flow = OptionsFlowHandler(mock_config_entry)

        selector = flow.sensor_selector

        assert selector is not None
        # Verify it's a select selector with expected options
        assert hasattr(selector, 'config')


class TestFormValidation:
    """Test form validation and schema."""

    @pytest.mark.asyncio
    async def test_illuminance_threshold_range(self, mock_config_entry):
        """Test illuminance threshold accepts valid range."""
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        # Test minimum value
        user_input = {
            CONFIG_IS_SLEEPING_AREA: False,
            CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 0,
        }
        result = await flow.async_step_init(user_input=user_input)
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        # Test maximum value
        user_input = {
            CONFIG_IS_SLEEPING_AREA: False,
            CONFIG_AUTO_LIGHTS_MAX_ILLUMINANCE: 1000,
        }
        result = await flow.async_step_init(user_input=user_input)
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_sleeping_area_boolean(self, mock_config_entry):
        """Test sleeping area accepts boolean values."""
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        for sleeping_value in [True, False]:
            user_input = {
                CONFIG_IS_SLEEPING_AREA: sleeping_value,
            }
            result = await flow.async_step_init(user_input=user_input)
            assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
            assert result["data"][CONFIG_IS_SLEEPING_AREA] == sleeping_value


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_options_flow_with_empty_options(self):
        """Test options flow handles entry with no options."""
        mock_config_entry = MagicMock(spec=config_entries.ConfigEntry)
        mock_config_entry.data = {CONFIG_AREA: "test_room_id"}
        mock_config_entry.options = {}  # Empty options

        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = MagicMock()

        with patch.object(flow, 'get_light_entities', return_value=[]):
            result = await flow.async_step_init(user_input=None)

        # Should handle gracefully and show form
        assert result["type"] == data_entry_flow.FlowResultType.FORM

    def test_validate_area_with_no_existing_data(self, mock_hass, mock_area_registry):
        """Test area validation when no existing areas configured."""
        with patch("custom_components.auto_areas.config_flow.ar.async_get") as mock_ar_get:
            mock_ar_get.return_value = mock_area_registry

            # No existing data
            mock_hass.data = {}

            flow = ConfigFlowHandler()
            flow.hass = mock_hass

            # Should succeed
            area = flow.validate_area("test_room_id")
            assert area is not None
