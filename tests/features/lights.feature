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