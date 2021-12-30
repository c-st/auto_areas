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
        When Component is started
        Then No presence is detected in area 'bedroom'
        And No presence is detected in area 'bathroom'

    Scenario: Single sensor turns on
        Given The state of all motion sensors is 'off'
        When State of motion sensor 2 is set to 'on'
        Then Presence is detected in area 'bedroom'
        And No presence is detected in area 'bathroom'

    Scenario: Multiple sensors turn on
        Given The state of all motion sensors is 'off'
        When State of motion sensor 2 is set to 'on'
        And State of motion sensor 3 is set to 'on'
        Then Presence is detected in area 'bedroom'
        And Presence is detected in area 'bathroom'

    Scenario: Presence is cleared
        Given The state of all motion sensors is 'on'
        When State of motion sensor 3 is set to 'off'
        Then No presence is detected in area 'bathroom'
        And Presence is detected in area 'bedroom'