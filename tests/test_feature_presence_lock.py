from functools import partial
import logging

import pytest_bdd
from pytest_bdd import scenario

_LOGGER = logging.getLogger(__name__)

scenario = partial(pytest_bdd.scenario, "features/presence_lock.feature")


@scenario("Presence lock turns on lights")
def test_presence_lock_turns_on_lights():
    pass


@scenario("Lights stay on with presence lock")
def test_lights_stay_on_with_presence_lock():
    pass
