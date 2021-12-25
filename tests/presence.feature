Feature: Presence tracking

Scenario: Handling multiple sensors
    Given There are some areas with entities assigned
    When the component is initialized
    Then an AutoArea should be setup for each area