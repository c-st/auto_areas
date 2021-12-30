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
        Given Sleep mode is off in the area 'bedroom'
        And The state of all motion sensors is 'off'
        When State of motion sensor 2 is set to 'on'
        Then Lights are on in area 'bedroom'

    Scenario: Lights stay off during sleep mode
        Given Sleep mode is on in the area 'bedroom'
        And The state of all motion sensors is 'off'
        When State of motion sensor 2 is set to 'on'
        Then Lights are off in area 'bedroom'
        And Presence is detected in area 'bedroom'

    Scenario: Lights turn off when sleep mode is turned on
        Given Sleep mode is off in the area 'bedroom'
        And The state of all motion sensors is 'on'
        When Sleep mode is on in the area 'bedroom'
        Then Lights are off in area 'bedroom'

    Scenario: Lights turn back on when sleep mode is turned off
        Given Sleep mode is on in the area 'bedroom'
        And The state of all motion sensors is 'off'
        And All lights are turned 'off'
        When Sleep mode is off in the area 'bedroom'
        And State of motion sensor 2 is set to 'on'
        Then Lights are on in area 'bedroom'
