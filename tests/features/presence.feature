Feature: Presence tracking
    All motion sensors in an area are used to evaluate presence.

    Background:
        Given There are the following areas:
            bedroom
            bathroom
        And There are motion sensors placed in these areas:
            bedroom
            bedroom
            bathroom

    Scenario: Initially off
        Given The state of all motion sensors is 'off'
        When component is started
        Then no presence is detected in area 'bedroom'
        And no presence is detected in area 'bathroom'

    Scenario: Single sensor turns on
        Given The state of all motion sensors is 'off'
        When state of motion sensor 2 is set to 'on'
        Then presence is detected in area 'bedroom'
        And no presence is detected in area 'bathroom'

    Scenario: Multiple sensors turn on
        Given The state of all motion sensors is 'off'
        When state of motion sensor 2 is set to 'on'
        And state of motion sensor 3 is set to 'on'
        Then presence is detected in area 'bedroom'
        And presence is detected in area 'bathroom'

    Scenario: Presence is cleared
        Given The state of all motion sensors is 'on'
        When state of motion sensor 3 is set to 'off'
        Then no presence is detected in area 'bathroom'
        And presence is detected in area 'bedroom'