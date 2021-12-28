# Auto Areas

> A custom component for [Home Assistant](https://www.home-assistant.io) which automates your areas.

An **area** could be a room or any part of your house ("garden", "hallway", etc.).
Assigning entities and devices to areas allows to create certain kind of automations **automatically**.

Example:

> Controlling lights in your rooms based on presence:
> In most of the cases you want the lights in a room to be turned on when presence is detected.
> Additionally you want the lights to turn off as soon as the occupancy is cleared.

Normally it would be necessary to set up automations for all sensors and lights for each of your areas (and also maintain them).

🤖 **Auto Areas** tries to make your life easier.

It checks each of your areas for relevant devices and starts managing them automatically. The only prerequisite is to assign them to areas in HomeAssistant.

## Features

### Aggregated presence detection

Track the state of multiple sensor entities (for example motion sensors) to detect area presence.

It aggregates presence based on these rules:
An area is considered "occupied" if there is at least one sensor in state `on` (for example "motion detected").
Only if all sensors are `off` the area presence is cleared and it is considered empty.

Supported entities:

- `binary_sensor` (with device class: `motion`, `occupancy`, `presence`)

[Scenarios (Gherkin)](tests/features/presence.feature)

### Control lights automatically

Turn lights on and off based on area presence.

### Behaviours

Control the behaviour of how your devices are managed.

- presence lock (treat a room as occupied regardless of sensor state)
- sleeping room (adds a sleep mode `switch`)
  - disable automatic light control (keep light off)
- ...

### Aggregate sensor data

Measurement values for `temperature`, `humidity`, `illuminance` from multiple devices are aggregated per area.

## Installation

Install as custom_component for HomeAssistant.

1. Place in `custom_components` folder of your Home Assistant installation. Or add as [custom repository](https://hacs.xyz/docs/faq/custom_repositories) in HACS.
2. Add an entry in `configuration.yaml`:

```yaml
auto_areas:
```

That's it (for now). Entities are auto-discovered based on the area they're assigned to in Home Assistant.

## Development

Install dependencies:
`pip install --disable-pip-version-check -r requirements_test.txt`

Run tests:
`pytest`

Using [DevContainer](https://code.visualstudio.com/docs/remote/containers) is recommended (see config in `.devcontainer`).

## Acknowledgements

Auto Areas is inspired by [Magic Areas](https://github.com/jseidl/hass-magic_areas).
