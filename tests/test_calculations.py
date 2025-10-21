"""Test calculation functions."""
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.components.sensor.const import SensorDeviceClass

from custom_components.auto_areas.calculations import (
    is_float,
    is_bool,
    calculate_max,
    calculate_min,
    calculate_mean,
    calculate_median,
    calculate_all,
    calculate_one,
    calculate_none,
    calculate_last,
    get_calculation,
    CALCULATE_MAX,
    CALCULATE_MIN,
    CALCULATE_MEAN,
    CALCULATE_MEDIAN,
    CALCULATE_ALL,
    CALCULATE_ONE,
    CALCULATE_NONE,
    CALCULATE_LAST,
    DEFAULT_CALCULATION_ILLUMINANCE,
    DEFAULT_CALCULATION_TEMPERATURE,
    DEFAULT_CALCULATION_HUMIDITY,
)
from custom_components.auto_areas.const import (
    CONFIG_ILLUMINANCE_CALCULATION,
    CONFIG_TEMPERATURE_CALCULATION,
    CONFIG_HUMIDITY_CALCULATION,
)


def create_state(value, last_updated=None):
    """Create a mock state object."""
    state = MagicMock()
    state.state = value
    state.last_updated = last_updated or datetime.now()
    return state


class TestIsFloat:
    """Test is_float function."""

    def test_valid_float_string(self):
        """Test with valid float string."""
        state = create_state("123.45")
        assert is_float(state) is True

    def test_valid_integer_string(self):
        """Test with valid integer string."""
        state = create_state("42")
        assert is_float(state) is True

    def test_negative_number(self):
        """Test with negative number."""
        state = create_state("-10.5")
        assert is_float(state) is True

    def test_invalid_string(self):
        """Test with invalid string."""
        state = create_state("not_a_number")
        assert is_float(state) is False

    def test_none_value(self):
        """Test with None value."""
        state = create_state(None)
        assert is_float(state) is False

    def test_unavailable_state(self):
        """Test with unavailable state."""
        state = create_state(STATE_UNAVAILABLE)
        assert is_float(state) is False


class TestIsBool:
    """Test is_bool function."""

    def test_on_state(self):
        """Test with 'on' state."""
        state = create_state("on")
        assert is_bool(state) is True

    def test_yes_state(self):
        """Test with 'yes' state."""
        state = create_state("yes")
        assert is_bool(state) is True

    def test_true_string(self):
        """Test with 'true' string."""
        state = create_state("true")
        assert is_bool(state) is True

    def test_one_string(self):
        """Test with '1' string."""
        state = create_state("1")
        assert is_bool(state) is True

    def test_true_bool(self):
        """Test with True boolean."""
        state = create_state(True)
        assert is_bool(state) is True

    def test_one_int(self):
        """Test with 1 integer."""
        state = create_state(1)
        assert is_bool(state) is True

    def test_off_state(self):
        """Test with 'off' state."""
        state = create_state("off")
        assert is_bool(state) is False

    def test_false_bool(self):
        """Test with False boolean."""
        state = create_state(False)
        assert is_bool(state) is False

    def test_number(self):
        """Test with number."""
        state = create_state("42")
        assert is_bool(state) is False


class TestCalculateMax:
    """Test calculate_max function."""

    def test_max_of_values(self):
        """Test maximum calculation."""
        states = [
            create_state("10"),
            create_state("25"),
            create_state("15"),
        ]
        result = calculate_max(states)
        assert result == 25

    def test_max_with_floats(self):
        """Test maximum with float values."""
        states = [
            create_state("10.5"),
            create_state("25.2"),
            create_state("15.8"),
        ]
        result = calculate_max(states)
        assert result == 25.2

    def test_max_with_negative(self):
        """Test maximum with negative values."""
        states = [
            create_state("-10"),
            create_state("-5"),
            create_state("-20"),
        ]
        result = calculate_max(states)
        assert result == -5

    def test_max_empty_list(self):
        """Test maximum with empty list."""
        result = calculate_max([])
        assert result == STATE_UNKNOWN

    def test_max_with_invalid_states(self):
        """Test maximum with invalid states."""
        states = [
            create_state("invalid"),
            create_state(STATE_UNAVAILABLE),
        ]
        result = calculate_max(states)
        assert result == STATE_UNKNOWN

    def test_max_mixed_valid_invalid(self):
        """Test maximum with mixed valid and invalid states."""
        states = [
            create_state("10"),
            create_state("invalid"),
            create_state("25"),
        ]
        result = calculate_max(states)
        assert result == 25


class TestCalculateMin:
    """Test calculate_min function."""

    def test_min_of_values(self):
        """Test minimum calculation."""
        states = [
            create_state("10"),
            create_state("25"),
            create_state("15"),
        ]
        result = calculate_min(states)
        assert result == 10

    def test_min_with_floats(self):
        """Test minimum with float values."""
        states = [
            create_state("10.5"),
            create_state("5.2"),
            create_state("15.8"),
        ]
        result = calculate_min(states)
        assert result == 5.2

    def test_min_empty_list(self):
        """Test minimum with empty list."""
        result = calculate_min([])
        assert result == STATE_UNKNOWN

    def test_min_with_invalid_states(self):
        """Test minimum with invalid states."""
        states = [
            create_state("invalid"),
        ]
        result = calculate_min(states)
        assert result == STATE_UNKNOWN


class TestCalculateMean:
    """Test calculate_mean function."""

    def test_mean_of_values(self):
        """Test mean calculation."""
        states = [
            create_state("10"),
            create_state("20"),
            create_state("30"),
        ]
        result = calculate_mean(states)
        assert result == 20

    def test_mean_with_floats(self):
        """Test mean with float values."""
        states = [
            create_state("10.5"),
            create_state("20.5"),
        ]
        result = calculate_mean(states)
        assert result == 15.5

    def test_mean_empty_list(self):
        """Test mean with empty list."""
        result = calculate_mean([])
        assert result == STATE_UNKNOWN

    def test_mean_single_value(self):
        """Test mean with single value."""
        states = [create_state("42")]
        result = calculate_mean(states)
        assert result == 42


class TestCalculateMedian:
    """Test calculate_median function."""

    def test_median_odd_count(self):
        """Test median with odd number of values."""
        states = [
            create_state("10"),
            create_state("20"),
            create_state("30"),
        ]
        result = calculate_median(states)
        assert result == 20

    def test_median_even_count(self):
        """Test median with even number of values."""
        states = [
            create_state("10"),
            create_state("20"),
            create_state("30"),
            create_state("40"),
        ]
        result = calculate_median(states)
        assert result == 25

    def test_median_empty_list(self):
        """Test median with empty list."""
        result = calculate_median([])
        assert result == STATE_UNKNOWN

    def test_median_single_value(self):
        """Test median with single value."""
        states = [create_state("42")]
        result = calculate_median(states)
        assert result == 42


class TestCalculateAll:
    """Test calculate_all function."""

    def test_all_true(self):
        """Test when all values are true."""
        states = [
            create_state("on"),
            create_state("yes"),
            create_state("true"),
        ]
        result = calculate_all(states)
        assert result is True

    def test_all_false(self):
        """Test when all values are false."""
        states = [
            create_state("off"),
            create_state("no"),
        ]
        result = calculate_all(states)
        assert result is False

    def test_mixed_values(self):
        """Test with mixed true/false values."""
        states = [
            create_state("on"),
            create_state("off"),
        ]
        result = calculate_all(states)
        assert result is False

    def test_all_empty_list(self):
        """Test with empty list."""
        result = calculate_all([])
        assert result == STATE_UNKNOWN


class TestCalculateOne:
    """Test calculate_one function."""

    def test_one_true(self):
        """Test when at least one value is true."""
        states = [
            create_state("on"),
            create_state("off"),
        ]
        result = calculate_one(states)
        assert result is True

    def test_all_false(self):
        """Test when all values are false."""
        states = [
            create_state("off"),
            create_state("no"),
        ]
        result = calculate_one(states)
        assert result is False

    def test_all_true(self):
        """Test when all values are true."""
        states = [
            create_state("on"),
            create_state("yes"),
        ]
        result = calculate_one(states)
        assert result is True

    def test_one_empty_list(self):
        """Test with empty list."""
        result = calculate_one([])
        assert result == STATE_UNKNOWN


class TestCalculateNone:
    """Test calculate_none function."""

    def test_none_true(self):
        """Test when no values are true."""
        states = [
            create_state("off"),
            create_state("no"),
        ]
        result = calculate_none(states)
        assert result is True

    def test_one_true(self):
        """Test when one value is true."""
        states = [
            create_state("on"),
            create_state("off"),
        ]
        result = calculate_none(states)
        assert result is False

    def test_all_true(self):
        """Test when all values are true."""
        states = [
            create_state("on"),
            create_state("yes"),
        ]
        result = calculate_none(states)
        assert result is False

    def test_none_empty_list(self):
        """Test with empty list."""
        result = calculate_none([])
        assert result == STATE_UNKNOWN


class TestCalculateLast:
    """Test calculate_last function."""

    def test_last_updated(self):
        """Test getting the last updated value."""
        now = datetime.now()
        states = [
            create_state("old", now - timedelta(hours=2)),
            create_state("newest", now),
            create_state("middle", now - timedelta(hours=1)),
        ]
        result = calculate_last(states)
        assert result == "newest"

    def test_last_with_unavailable(self):
        """Test with unavailable states."""
        now = datetime.now()
        states = [
            create_state("old", now - timedelta(hours=1)),
            create_state(STATE_UNAVAILABLE, now),
            create_state(STATE_UNKNOWN, now + timedelta(seconds=1)),
        ]
        result = calculate_last(states)
        assert result == "old"

    def test_last_empty_list(self):
        """Test with empty list."""
        result = calculate_last([])
        assert result == STATE_UNKNOWN

    def test_last_all_invalid(self):
        """Test when all states are invalid."""
        states = [
            create_state(STATE_UNAVAILABLE),
            create_state(STATE_UNKNOWN),
            create_state(None),
        ]
        result = calculate_last(states)
        assert result == STATE_UNKNOWN


class TestGetCalculation:
    """Test get_calculation function."""

    def test_illuminance_default(self):
        """Test illuminance with default calculation."""
        config = {}
        func = get_calculation(config, SensorDeviceClass.ILLUMINANCE)
        assert func == calculate_last

    def test_illuminance_custom(self):
        """Test illuminance with custom calculation."""
        config = {CONFIG_ILLUMINANCE_CALCULATION: CALCULATE_MAX}
        func = get_calculation(config, SensorDeviceClass.ILLUMINANCE)
        assert func == calculate_max

    def test_temperature_default(self):
        """Test temperature with default calculation."""
        config = {}
        func = get_calculation(config, SensorDeviceClass.TEMPERATURE)
        assert func == calculate_mean

    def test_temperature_custom(self):
        """Test temperature with custom calculation."""
        config = {CONFIG_TEMPERATURE_CALCULATION: CALCULATE_MIN}
        func = get_calculation(config, SensorDeviceClass.TEMPERATURE)
        assert func == calculate_min

    def test_humidity_default(self):
        """Test humidity with default calculation."""
        config = {}
        func = get_calculation(config, SensorDeviceClass.HUMIDITY)
        assert func == calculate_max

    def test_humidity_custom(self):
        """Test humidity with custom calculation."""
        config = {CONFIG_HUMIDITY_CALCULATION: CALCULATE_MEDIAN}
        func = get_calculation(config, SensorDeviceClass.HUMIDITY)
        assert func == calculate_median

    def test_unsupported_sensor_type(self):
        """Test with unsupported sensor type."""
        config = {}
        func = get_calculation(config, SensorDeviceClass.PRESSURE)
        assert func is None

    def test_invalid_calculation_method(self):
        """Test with invalid calculation method."""
        config = {CONFIG_ILLUMINANCE_CALCULATION: "invalid_method"}
        func = get_calculation(config, SensorDeviceClass.ILLUMINANCE)
        assert func is None


class TestConstants:
    """Test calculation constants."""

    def test_default_illuminance(self):
        """Test default illuminance calculation."""
        assert DEFAULT_CALCULATION_ILLUMINANCE == CALCULATE_LAST

    def test_default_temperature(self):
        """Test default temperature calculation."""
        assert DEFAULT_CALCULATION_TEMPERATURE == CALCULATE_MEAN

    def test_default_humidity(self):
        """Test default humidity calculation."""
        assert DEFAULT_CALCULATION_HUMIDITY == CALCULATE_MAX

    def test_calculation_constants(self):
        """Test calculation method constants."""
        assert CALCULATE_MAX == "max"
        assert CALCULATE_MIN == "min"
        assert CALCULATE_MEAN == "mean"
        assert CALCULATE_MEDIAN == "median"
        assert CALCULATE_LAST == "last"
        assert CALCULATE_ALL == "all"
        assert CALCULATE_ONE == "one"
        assert CALCULATE_NONE == "none"
