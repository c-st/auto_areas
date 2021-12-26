import logging
from functools import partial

import pytest_bdd

from pytest_bdd import scenario

_LOGGER = logging.getLogger(__name__)

scenario = partial(pytest_bdd.scenario, "features/presence.feature")


@scenario("Initially off")
def test_initally_off():
    pass


@scenario("Single sensor turns on")
def test_multiple_sensors():
    pass


@scenario("Multiple sensors turn on")
def test_multiple_sensors_on():
    pass


# @scenario("Presence is cleared")
# def test_presence_is_cleared():
#     pass
