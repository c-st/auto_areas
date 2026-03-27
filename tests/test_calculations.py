"""Tests for calculation functions."""

from unittest.mock import MagicMock
from datetime import datetime, timezone


STATE_UNKNOWN = "unknown"
STATE_UNAVAILABLE = "unavailable"


def _make_state(state_value, last_updated=None):
    """Create a mock HA State object."""
    state = MagicMock()
    state.state = state_value
    state.last_updated = last_updated or datetime.now(tz=timezone.utc)
    return state


class TestCalculateMax:
    """Test calculate_max."""

    def test_normal_values(self):
        """Test normal values."""
        from custom_components.auto_areas.calculations import calculate_max

        states = [_make_state("10.0"), _make_state("20.5"), _make_state("15.3")]
        assert calculate_max(states) == 20.5

    def test_empty_list(self):
        """Test empty list."""
        from custom_components.auto_areas.calculations import calculate_max

        assert calculate_max([]) == STATE_UNKNOWN

    def test_mixed_numeric_non_numeric(self):
        """Test mixed numeric non numeric."""
        from custom_components.auto_areas.calculations import calculate_max

        states = [_make_state("10.0"), _make_state("not_a_number"), _make_state("20.0")]
        assert calculate_max(states) == 20.0


class TestCalculateMin:
    """Test calculate_min."""

    def test_normal_values(self):
        """Test normal values."""
        from custom_components.auto_areas.calculations import calculate_min

        states = [_make_state("10.0"), _make_state("20.5"), _make_state("15.3")]
        assert calculate_min(states) == 10.0

    def test_empty_list(self):
        """Test empty list."""
        from custom_components.auto_areas.calculations import calculate_min

        assert calculate_min([]) == STATE_UNKNOWN

    def test_mixed_numeric_non_numeric(self):
        """Test mixed numeric non numeric."""
        from custom_components.auto_areas.calculations import calculate_min

        states = [_make_state("10.0"), _make_state("not_a_number"), _make_state("5.0")]
        assert calculate_min(states) == 5.0


class TestCalculateMean:
    """Test calculate_mean."""

    def test_normal_values(self):
        """Test normal values."""
        from custom_components.auto_areas.calculations import calculate_mean

        states = [_make_state("10.0"), _make_state("20.0"), _make_state("30.0")]
        assert calculate_mean(states) == 20.0

    def test_single_value(self):
        """Test single value."""
        from custom_components.auto_areas.calculations import calculate_mean

        states = [_make_state("42.0")]
        assert calculate_mean(states) == 42.0

    def test_empty_list(self):
        """Test empty list."""
        from custom_components.auto_areas.calculations import calculate_mean

        assert calculate_mean([]) == STATE_UNKNOWN


class TestCalculateMedian:
    """Test calculate_median."""

    def test_odd_number_of_values(self):
        """Test odd number of values."""
        from custom_components.auto_areas.calculations import calculate_median

        states = [_make_state("10.0"), _make_state("20.0"), _make_state("30.0")]
        assert calculate_median(states) == 20.0

    def test_even_number_of_values(self):
        """Test even number of values."""
        from custom_components.auto_areas.calculations import calculate_median

        states = [_make_state("10.0"), _make_state("20.0"), _make_state("30.0"), _make_state("40.0")]
        assert calculate_median(states) == 25.0

    def test_empty_list(self):
        """Test empty list."""
        from custom_components.auto_areas.calculations import calculate_median

        assert calculate_median([]) == STATE_UNKNOWN


class TestCalculateAll:
    """Test calculate_all (boolean AND)."""

    def test_all_true(self):
        """Test all true."""
        from custom_components.auto_areas.calculations import calculate_all

        states = [_make_state("on"), _make_state("on"), _make_state("on")]
        assert calculate_all(states) is True

    def test_some_false(self):
        """When mixing truthy and non-truthy booleans.

        is_bool only passes truthy values (on, yes, true, 1), so calculate_all
        can only return True or UNKNOWN with those inputs.
        """
        from custom_components.auto_areas.calculations import calculate_all

        # "on" passes is_bool and is truthy; "off" is filtered out
        # So with ["on", "off", "on"], only ["on", "on"] remain -> all truthy -> True
        states = [_make_state("on"), _make_state("off"), _make_state("on")]
        assert calculate_all(states) is True

    def test_all_false(self):
        """Test all false."""
        from custom_components.auto_areas.calculations import calculate_all

        states = [_make_state("off"), _make_state("off")]
        # "off" is not in the is_bool truthy list, so filtered out -> empty -> UNKNOWN
        assert calculate_all(states) == STATE_UNKNOWN

    def test_empty(self):
        """Test empty."""
        from custom_components.auto_areas.calculations import calculate_all

        assert calculate_all([]) == STATE_UNKNOWN


class TestCalculateOne:
    """Test calculate_one (boolean OR)."""

    def test_one_true(self):
        """Test one true."""
        from custom_components.auto_areas.calculations import calculate_one

        states = [_make_state("off"), _make_state("on"), _make_state("off")]
        # "off" is filtered by is_bool, "on" passes
        assert calculate_one(states) is True

    def test_none_true(self):
        """Test none true."""
        from custom_components.auto_areas.calculations import calculate_one

        states = [_make_state("off"), _make_state("off")]
        # "off" doesn't pass is_bool -> empty -> UNKNOWN
        assert calculate_one(states) == STATE_UNKNOWN

    def test_all_true(self):
        """Test all true."""
        from custom_components.auto_areas.calculations import calculate_one

        states = [_make_state("on"), _make_state("on")]
        assert calculate_one(states) is True

    def test_empty(self):
        """Test empty."""
        from custom_components.auto_areas.calculations import calculate_one

        assert calculate_one([]) == STATE_UNKNOWN


class TestCalculateNone:
    """Test calculate_none (boolean NOR)."""

    def test_none_true(self):
        """Test none true."""
        from custom_components.auto_areas.calculations import calculate_none

        # "off" doesn't pass is_bool -> empty -> UNKNOWN
        states = [_make_state("off"), _make_state("off")]
        assert calculate_none(states) == STATE_UNKNOWN

    def test_some_true(self):
        """Test some true."""
        from custom_components.auto_areas.calculations import calculate_none

        states = [_make_state("on"), _make_state("off")]
        # "on" passes is_bool and is truthy -> not all non-truthy
        assert calculate_none(states) is False

    def test_empty(self):
        """Test empty."""
        from custom_components.auto_areas.calculations import calculate_none

        assert calculate_none([]) == STATE_UNKNOWN

    def test_all_on(self):
        """Test all on."""
        from custom_components.auto_areas.calculations import calculate_none

        states = [_make_state("on"), _make_state("on")]
        assert calculate_none(states) is False


class TestCalculateLast:
    """Test calculate_last (most recently updated)."""

    def test_returns_most_recent(self):
        """Test returns most recent."""
        from custom_components.auto_areas.calculations import calculate_last

        old_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        new_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        states = [
            _make_state("21.0", last_updated=old_time),
            _make_state("23.5", last_updated=new_time),
        ]
        assert calculate_last(states) == "23.5"

    def test_excludes_unavailable(self):
        """Test excludes unavailable."""
        from custom_components.auto_areas.calculations import calculate_last

        old_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        new_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        states = [
            _make_state("21.0", last_updated=old_time),
            _make_state(STATE_UNAVAILABLE, last_updated=new_time),
        ]
        assert calculate_last(states) == "21.0"

    def test_excludes_unknown(self):
        """Test excludes unknown."""
        from custom_components.auto_areas.calculations import calculate_last

        old_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        new_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        states = [
            _make_state("18.0", last_updated=old_time),
            _make_state(STATE_UNKNOWN, last_updated=new_time),
        ]
        assert calculate_last(states) == "18.0"

    def test_empty(self):
        """Test empty."""
        from custom_components.auto_areas.calculations import calculate_last

        assert calculate_last([]) == STATE_UNKNOWN


class TestGetCalculation:
    """Test get_calculation returns correct function per sensor type."""

    def test_temperature_default(self):
        """Test temperature default."""
        from custom_components.auto_areas.calculations import (
            get_calculation, calculate_mean,
        )
        from homeassistant.components.sensor.const import SensorDeviceClass

        fn = get_calculation({}, SensorDeviceClass.TEMPERATURE)
        assert fn is calculate_mean

    def test_humidity_default(self):
        """Test humidity default."""
        from custom_components.auto_areas.calculations import (
            get_calculation, calculate_max,
        )
        from homeassistant.components.sensor.const import SensorDeviceClass

        fn = get_calculation({}, SensorDeviceClass.HUMIDITY)
        assert fn is calculate_max

    def test_illuminance_default(self):
        """Test illuminance default."""
        from custom_components.auto_areas.calculations import (
            get_calculation, calculate_last,
        )
        from homeassistant.components.sensor.const import SensorDeviceClass

        fn = get_calculation({}, SensorDeviceClass.ILLUMINANCE)
        assert fn is calculate_last

    def test_unknown_sensor_type_returns_none(self):
        """Test unknown sensor type returns none."""
        from custom_components.auto_areas.calculations import get_calculation
        from homeassistant.components.sensor.const import SensorDeviceClass

        fn = get_calculation({}, SensorDeviceClass.PRESSURE)
        assert fn is None

    def test_config_override(self):
        """Test config override."""
        from custom_components.auto_areas.calculations import (
            get_calculation, calculate_min,
        )
        from custom_components.auto_areas.const import CONFIG_TEMPERATURE_CALCULATION
        from homeassistant.components.sensor.const import SensorDeviceClass

        fn = get_calculation(
            {CONFIG_TEMPERATURE_CALCULATION: "min"},
            SensorDeviceClass.TEMPERATURE,
        )
        assert fn is calculate_min
