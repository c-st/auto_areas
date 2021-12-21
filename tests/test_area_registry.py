from pytest_bdd import scenario, given, when, then


@scenario("area_registry.feature", "Configuring entities")
def test_publish():
    pass


@given("There are some areas with entities assigned", target_fixture="article")
def article():
    return


@when("the component is initialized")
def go_to_article():
    return


@then("an AutoArea should be setup for each area")
def no_error_message():
    assert 1 == 2
    return
