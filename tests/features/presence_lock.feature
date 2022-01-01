Feature: Presence lock
    Presence lock can be used to treat an areas as occupied regardless of sensor state.

    Background:
        Given There are the following areas:
            living room
            bedroom
        And There are motion sensors placed in these areas:
            living room
            bedroom
        And There are lights placed in these areas:
           living room
           bedroom

    Scenario: Presence lock turns on lights
        Given The state of all motion sensors is 'off'
        When Presence lock is 'on' in area 'living room'
        Then Presence is detected in area 'living room'
        And Lights are on in area 'living room'

    Scenario: Lights stay on with presence lock
        Given The state of all motion sensors is 'on'
        When Presence lock is 'on' in area 'living room'
        And State of motion sensor 1 is set to 'off'
        Then Presence is detected in area 'living room'
        And Lights are on in area 'living room'