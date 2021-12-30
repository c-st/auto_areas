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

    # Scenario: Lights stay off during sleep mode
    #     Given sleep mode is on for the area "bedroom"
    #     And The state of all motion sensors is "off"
    #     When state of motion sensor 2 is set to 'on'
    #     Then lights are off in area "bedroom"
    #     And presence is detected in area "bedroom"