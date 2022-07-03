from functools import partial
import logging

import pytest_bdd
from pytest_bdd import scenario

_LOGGER = logging.getLogger(__name__)

scenario = partial(pytest_bdd.scenario, "features/scene_activation.feature")


@scenario("Presence scene is activated")
def test_presence_scene_is_activated():
    pass


@scenario("Goodbye scene is activated")
def test_goodbye_scene_is_activated():
    pass


# @scenario("Sleep scene is activated")
# def test_sleep_scene_is_activated():
#     pass
