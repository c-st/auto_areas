"""Perform calculations based on entity states."""

from statistics import mean, median
from homeassistant.core import State
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.helpers.typing import StateType


def calculate_max(states: list[State]) -> StateType:
    """Calculate the maximum of the list of values."""
    calc_values = [float(s.state) for s in states]

    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return max(calc_values)


def calculate_min(states: list[State]) -> StateType:
    """Calculate the mean of the list of values."""
    calc_values = [float(s.state) for s in states]

    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return min(calc_values)


def calculate_mean(states: list[State]) -> StateType:
    """Calculate the mean of the list of values."""
    calc_values = [float(s.state) for s in states]

    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return mean(calc_values)


def calculate_median(states: list[State]) -> StateType:
    """Calculate the median of the list of values."""
    calc_values = [float(s.state) for s in states]

    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return median(calc_values)


def calculate_all(states: list[State]) -> StateType:
    """Calculate whether all of the list of values are true."""
    calc_values = [s.state for s in states if isinstance(s.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if not v]) == 0


def calculate_one(states: list[State]) -> StateType:
    """Calculate whether one of the list of values is true."""
    calc_values = [s.state for s in states if isinstance(s.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if v]) > 0


def calculate_none(states: list[State]) -> StateType:
    """Calculate whether none of the list of values is true."""
    calc_values = [s.state for s in states if isinstance(s.state, bool)]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return len([v for v in calc_values if v]) == 0


def calculate_last(states: list[State]) -> StateType:
    """Calculate the last update of the list of values."""
    calc_values = [s for s in states if s.state is not None and s.state not in [
        STATE_UNKNOWN, STATE_UNAVAILABLE]]
    if len(calc_values) == 0:
        return STATE_UNKNOWN
    return sorted(calc_values, key=lambda v: v.last_updated, reverse=True)[0].state
