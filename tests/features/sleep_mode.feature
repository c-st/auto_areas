Feature: Sleep mode
    Automatic light control can be customized with sleep mode.

    Background:
        Given There are the following areas:
            living room
            bedroom
        And The area 'bedroom' is marked as sleeping area
        And There are motion sensors placed in these areas:
            living room
            bedroom
        And There are lights placed in these areas:
           living room
           bedroom

    Scenario: Lights are controlled automatically with sleep mode turned off
        Given sleep mode is off in the area 'bedroom'
        And the state of all motion sensors is 'off'
        When state of motion sensor 2 is set to 'on'
        Then lights are on in area 'bedroom'

    Scenario: Lights stay off during sleep mode
        Given sleep mode is on in the area 'bedroom'
        And The state of all motion sensors is 'off'
        When state of motion sensor 2 is set to 'on'
        Then lights are off in area 'bedroom'
        And presence is detected in area 'bedroom'

    Scenario: Lights turn off when sleep mode is turned on
        Given sleep mode is off in the area 'bedroom'
        And The state of all motion sensors is 'on'
        When sleep mode is on in the area 'bedroom'
        Then lights are off in area 'bedroom'