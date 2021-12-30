# 🤖 Auto Areas

> _A custom component for [Home Assistant](https://www.home-assistant.io) which **automates** your **areas**._

An **area** could represent a room or any other part of your home. Relevant entities and devices can be assigned to these areas; making it possible to create certain kind of automations **automatically**.

Example setup of areas and entities:

```
- Living room
  - Motion sensor
  - Another motion sensor
  - Multiple lights
- Bedroom
  - Motion sensor
  - Light
- Bathroom
  - Motion sensor
  - Light
- Garden
  - Multiple lights
```

Desired behaviour:

- if there is one or more motion sensors assigned to a room, they are used to determine if it is currently occupied
- the lights in this room should be turned on if presence is detected
- once no more presence is detected, the lights should turn off again

To achieve this, without this component, it would be necessary to set up [automations](https://www.home-assistant.io/docs/automation/) for all sensors and lights for each of these areas.

🤖 **Auto Areas** can take over some of this work:

It checks each of your areas for relevant devices and starts managing them automatically.

The only requirements for your Home Assistant setup are:

- there are areas defined
- relevant entities (and devices) are assigned to these areas

For information on how to install this component refer to [Installation](#installation).

## Features

### Aggregated presence detection

Tracks the state of multiple sensor entities (for example motion sensors) to detect area presence.
It aggregates presence based on these rules:

- An area is considered "occupied" if there is at least one sensor in state `on` (for example motion is detected).
- Only if all sensors are `off` the area presence is cleared and the area is considered empty.

Currently the following entities are supported:

- `binary_sensor` (with device class: `motion`, `occupancy`, `presence`)

The presence state is published to a `binary_sensor` which will be named according to the area: `binary_sensor.area_presence_{area_name}`.

#### Presence lock

If only relying on motion sensors, presence could be cleared if there is only little or no movement. Presence lock can be used to treat an area as "occupied" regardless of sensor state.

A new switch with ID `switch.area_presence_lock_{area_name}` is created for each area. If the switch is `on`, lights will not be turned off.

[Scenarios (Gherkin)](tests/features/presence.feature)

### Control lights automatically

Turns lights on and off based on area presence.

[Scenarios (Gherkin)](tests/features/auto_lights.feature)

#### Sleep mode

For areas marked as "sleeping area", automatic light control can be temporarily turned off. Lights are never turned on even if presence is detected.

A switch with ID `switch.auto_sleep_mode_{area_name}` is created for each sleeping area.
If the switch is turned `on`, automatic light control will be disabled and lights will stay off.

For information on how to configure this feature refer to the [configuration section](#configuration).

[Scenarios (Gherkin)](tests/features/sleep_mode.feature)

### Aggregate sensor data

Measurement values for `temperature`, `humidity`, `illuminance` from multiple devices are aggregated per area.

## Installation

Install as custom_component for HomeAssistant.

1. Place in `custom_components` folder of your Home Assistant installation. Or add as [custom repository](https://hacs.xyz/docs/faq/custom_repositories) in HACS.
2. Add an entry in `configuration.yaml`:

```yaml
auto_areas:
```

Entities are auto-discovered based on the area they're assigned to in Home Assistant.

## Configuration

The behaviour of areas can be customised by adding additional configuration in YAML.

Using the (normalised) name of the area as key additional options can be enabled. In the following example the area with name `bedroom` is marked as sleeping area:

```yaml
# configuration.yaml

auto_areas:
  bedroom:
    is_sleeping_area: true
```

| Area option        | Description                                                                                         | Default value      |
| ------------------ | :-------------------------------------------------------------------------------------------------- | ------------------ |
| `is_sleeping_area` | Mark area as sleeping area. A switch for controlling sleep mode is created. [See more](#sleep-mode) | `false` (disabled) |

Created entities:

| Name                                      | Description                      |
| ----------------------------------------- | :------------------------------- |
| `binary_sensor.area_presence_{area_name}` |                                  |
| `switch.area_sleep_mode_{area_name}`      | Only created for sleeping areas. |

## Development

Install dependencies:
`pip install --disable-pip-version-check -r requirements_test.txt`

Run tests:
`pytest`

Using [DevContainer](https://code.visualstudio.com/docs/remote/containers) is recommended (see config in `.devcontainer`).

## Acknowledgements

Auto Areas is inspired by [Magic Areas](https://github.com/jseidl/hass-magic_areas).
