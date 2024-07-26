from typing import Any
from numbers import Number
from statistics import mean, median
from homeassistant.core import State
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.helpers.typing import StateType


def is_numeric(value: Any) -> bool:
    """Checks if the value is numeric."""
    try:
        if float(value) is not None:
            return True
    except:
        return False
    else:
        return False


def calculate_max(values: list[State]) -> StateType:
    """Calculate the maximum of the list of values."""
    calc_values = [float(v.state) for v in values if isinstance(
        v, Number) and not isinstance(v.state, bool) and is_numeric(v)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return max(calc_values)


def calculate_min(values: list[State]) -> StateType:
    """Calculate the mean of the list of values."""
    calc_values = [float(v.state) for v in values if isinstance(
        v, Number) and not isinstance(v.state, bool) and is_numeric(v)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return min(calc_values)


def calculate_mean(values: list[State]) -> StateType:
    """Calculate the mean of the list of values."""
    calc_values = [float(v.state) for v in values if isinstance(
        v, Number) and not isinstance(v.state, bool) and is_numeric(v)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return mean(calc_values)


def calculate_median(values: list[State]) -> StateType:
    """Calculate the median of the list of values."""
    calc_values = [float(v.state) for v in values if isinstance(
        v, Number) and not isinstance(v.state, bool) and is_numeric(v)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return median(calc_values)


def calculate_all(values: list[State]) -> StateType:
    """Calculate the whether all of the list of values are true."""
    calc_values = [v.state for v in values if isinstance(v.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if not v]) == 0


def calculate_one(values: list[State]) -> StateType:
    """Calculate the whether one of the list of values is true."""
    calc_values = [v.state for v in values if isinstance(v.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if v]) > 0


def calculate_none(values: list[State]) -> StateType:
    """Calculate the whether none of the list of values is true."""
    calc_values = [v.state for v in values if isinstance(v.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if v]) == 0


def calculate_last(values: list[State]) -> StateType:
    """Calculate the last update of the list of values."""
    calc_values = [v for v in values if v.state is not None and v.state not in [
        STATE_UNKNOWN, STATE_UNAVAILABLE]]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return sorted(calc_values, key=lambda v: v.last_updated, reverse=True)[0].state
