"""Test sensor entities."""
from unittest.mock import MagicMock
import pytest
from homeassistant.components.sensor.const import SensorDeviceClass

from custom_components.auto_areas.sensors.temperature import TemperatureSensor
from custom_components.auto_areas.sensors.humidity import HumiditySensor
from custom_components.auto_areas.sensors.illuminance import IlluminanceSensor


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.config = MagicMock()
    hass.config.units = MagicMock()
    hass.config.units.temperature_unit = "°C"
    return hass


@pytest.fixture
def mock_auto_area():
    """Create a mock AutoArea."""
    auto_area = MagicMock()
    auto_area.area_name = "Test Room"
    auto_area.slugified_area_name = "test_room"
    auto_area.config_entry = MagicMock()
    auto_area.config_entry.entry_id = "test_entry_id"
    auto_area.config_entry.options = {}
    auto_area.device_info = {
        "identifiers": {("auto_areas", "test_entry_id")},
        "name": "Test Room Auto Areas",
    }
    auto_area.get_valid_entities = MagicMock(return_value=[])
    return auto_area


class TestTemperatureSensor:
    """Test TemperatureSensor."""

    def test_initialization(self, mock_hass, mock_auto_area):
        """Test sensor initialization."""
        sensor = TemperatureSensor(mock_hass, mock_auto_area)

        assert sensor.hass == mock_hass
        assert sensor.auto_area == mock_auto_area

    def test_device_class(self, mock_hass, mock_auto_area):
        """Test sensor device class."""
        sensor = TemperatureSensor(mock_hass, mock_auto_area)

        assert sensor.device_class == SensorDeviceClass.TEMPERATURE

    def test_native_unit_of_measurement(self, mock_hass, mock_auto_area):
        """Test native unit of measurement."""
        sensor = TemperatureSensor(mock_hass, mock_auto_area)

        unit = sensor.native_unit_of_measurement
        assert unit == "°C"

    def test_native_unit_of_measurement_fahrenheit(
        self, mock_hass, mock_auto_area
    ):
        """Test native unit of measurement with Fahrenheit."""
        mock_hass.config.units.temperature_unit = "°F"
        sensor = TemperatureSensor(mock_hass, mock_auto_area)

        unit = sensor.native_unit_of_measurement
        assert unit == "°F"

    def test_state_initial(self, mock_hass, mock_auto_area):
        """Test initial state."""
        sensor = TemperatureSensor(mock_hass, mock_auto_area)

        # Initial aggregated state should be None
        assert sensor._aggregated_state is None
        assert sensor.state is None

    def test_unique_id(self, mock_hass, mock_auto_area):
        """Test unique ID generation."""
        sensor = TemperatureSensor(mock_hass, mock_auto_area)

        unique_id = sensor.unique_id
        assert "test_entry_id" in unique_id
        assert "temperature" in unique_id


class TestHumiditySensor:
    """Test HumiditySensor."""

    def test_initialization(self, mock_hass, mock_auto_area):
        """Test sensor initialization."""
        sensor = HumiditySensor(mock_hass, mock_auto_area)

        assert sensor.hass == mock_hass
        assert sensor.auto_area == mock_auto_area

    def test_device_class(self, mock_hass, mock_auto_area):
        """Test sensor device class."""
        sensor = HumiditySensor(mock_hass, mock_auto_area)

        assert sensor.device_class == SensorDeviceClass.HUMIDITY

    def test_native_unit_of_measurement(self, mock_hass, mock_auto_area):
        """Test native unit of measurement."""
        sensor = HumiditySensor(mock_hass, mock_auto_area)

        unit = sensor.native_unit_of_measurement
        assert unit == "%"

    def test_state_initial(self, mock_hass, mock_auto_area):
        """Test initial state."""
        sensor = HumiditySensor(mock_hass, mock_auto_area)

        assert sensor._aggregated_state is None
        assert sensor.state is None

    def test_unique_id(self, mock_hass, mock_auto_area):
        """Test unique ID generation."""
        sensor = HumiditySensor(mock_hass, mock_auto_area)

        unique_id = sensor.unique_id
        assert "test_entry_id" in unique_id
        assert "humidity" in unique_id


class TestIlluminanceSensor:
    """Test IlluminanceSensor."""

    def test_initialization(self, mock_hass, mock_auto_area):
        """Test sensor initialization."""
        sensor = IlluminanceSensor(mock_hass, mock_auto_area)

        assert sensor.hass == mock_hass
        assert sensor.auto_area == mock_auto_area

    def test_device_class(self, mock_hass, mock_auto_area):
        """Test sensor device class."""
        sensor = IlluminanceSensor(mock_hass, mock_auto_area)

        assert sensor.device_class == SensorDeviceClass.ILLUMINANCE

    def test_native_unit_of_measurement(self, mock_hass, mock_auto_area):
        """Test native unit of measurement."""
        sensor = IlluminanceSensor(mock_hass, mock_auto_area)

        unit = sensor.native_unit_of_measurement
        assert unit == "lx"

    def test_state_initial(self, mock_hass, mock_auto_area):
        """Test initial state."""
        sensor = IlluminanceSensor(mock_hass, mock_auto_area)

        assert sensor._aggregated_state is None
        assert sensor.state is None

    def test_unique_id(self, mock_hass, mock_auto_area):
        """Test unique ID generation."""
        sensor = IlluminanceSensor(mock_hass, mock_auto_area)

        unique_id = sensor.unique_id
        assert "test_entry_id" in unique_id
        assert "illuminance" in unique_id


class TestSensorCommon:
    """Test common sensor functionality."""

    def test_device_info_consistency(self, mock_hass, mock_auto_area):
        """Test that all sensors have consistent device info."""
        temp_sensor = TemperatureSensor(mock_hass, mock_auto_area)
        humidity_sensor = HumiditySensor(mock_hass, mock_auto_area)
        illuminance_sensor = IlluminanceSensor(mock_hass, mock_auto_area)

        assert temp_sensor.device_info == mock_auto_area.device_info
        assert humidity_sensor.device_info == mock_auto_area.device_info
        assert illuminance_sensor.device_info == mock_auto_area.device_info
