Feature: Automatic light control
    Lights are controlled per area based on presence state.

    Background:
        Given There are the following areas:
            living room
            bedroom
        And There are motion sensors placed in these areas:
            living room
            living room
            bedroom
        And There are lights placed in these areas:
           living room
           living room
           living room
           bedroom

    Scenario: Lights are off in areas without presence
        Given The state of all motion sensors is 'off'
        When component is started
        Then lights are off in area 'living room'
        And lights are off in area 'bedroom'

    Scenario: Lights are turned on if presence is detected
        Given The state of all motion sensors is 'off'
        When state of motion sensor 2 is set to 'on'
        Then lights are on in area 'living room'
        And lights are off in area 'bedroom'

    Scenario: Lights are turned off again if presence is cleared
        Given The state of all motion sensors is 'on'
        When state of motion sensor 3 is set to 'off'
        Then lights are on in area 'living room'
        And lights are off in area 'bedroom'