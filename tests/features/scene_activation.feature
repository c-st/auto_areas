Feature: Scene activation
    Automatic light control can be customized with a scene to be activated.

    Background:
        Given There are the following areas:
            bedroom
        And There are the following scenes:
            bedroom_presence
            bedroom_goodbye
            bedroom_sleep
        And There are motion sensors placed in these areas:
            bedroom
        And There are lights placed in these areas:
            bedroom

    Scenario: Presence scene is activated
        Given The area 'bedroom' has a 'presence' scene 'scene.bedroom_presence' configured
        And The state of all motion sensors is 'off'
        When state of motion sensor 1 is set to 'on'
        And entity states are evaluated
        Then The scene 'scene.bedroom_presence' has been activated
        And The scene 'scene.bedroom_goodbye' has not been activated

    Scenario: Goodbye scene is activated
        Given The area 'bedroom' has a 'goodbye' scene 'scene.bedroom_goodbye' configured
        And The state of all motion sensors is 'on'
        When state of motion sensor 1 is set to 'off'
        And entity states are evaluated
        Then The scene 'scene.bedroom_goodbye' has been activated
        And The scene 'scene.bedroom_presence' has not been activated

    # Scenario: Sleep scene is activated

