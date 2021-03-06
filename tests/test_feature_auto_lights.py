from functools import partial
import logging

import pytest_bdd
from pytest_bdd import scenario

_LOGGER = logging.getLogger(__name__)

scenario = partial(pytest_bdd.scenario, "features/auto_lights.feature")


@scenario("Lights are off in areas without presence")
def test_off_without_presence():
    pass


@scenario("Lights are turned on if presence is detected")
def test_on_with_presence():
    pass


@scenario("Lights are turned off again if presence is cleared")
def test_off_with_presence_cleared():
    pass
