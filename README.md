# 🤖 Auto Areas

> _A custom component for [Home Assistant](https://www.home-assistant.io) which **automates** your **areas**._

An **area** in Home Assistant can represent a room or any other part of your home. Relevant entities and devices can be assigned to these areas; making it possible to create certain kind of automations **automatically**.

Example setup of areas and entities:

```
- Living room
  - Motion sensor
  - Motion sensor 2
  - Light
  - Light 2
  - Light 3
- Bedroom
  - Motion sensor
  - Light
- Office
  - Motion sensor
  - Light
- Kitchen
  - Motion sensor
  - Light
```

Desired behaviour:

- if there is one or more motion sensors assigned to a room, all of them are used to determine if the room is currently occupied
- the lights in this room should be turned on if presence is detected
- once no presence is detected anymore the lights should turn off again

To achieve this, without this component, it would be necessary to set up [automations](https://www.home-assistant.io/docs/automation/) for all sensors and lights for each of the areas.

---

🤖 **Auto Areas** can take over some of this work:

It checks each of your areas for relevant devices and starts managing them automatically. Additionally, it creates a few sensors and switches which allow you to adjust its behaviour as needed.

For the example above the following entities would be created: ![created-entities](/resources/images/created_entities.png)

As auto-discovery is based on area-related information the requirements for your Home Assistant setup are:

- there is at least one area defined
- it has relevant entities assigned (at least a motion sensor and a light)

For information on how to install this component see [Installation](#installation).

## Features

### Aggregated presence detection

Tracks the state of multiple sensor entities (for example motion sensors) to detect area presence.
It aggregates presence based on these rules:

- An area is considered "occupied" if there is at least one sensor in state `on` (for example motion is detected)
- Only if all sensors are `off` the area presence is cleared and the area is considered empty

Currently `binary_sensor` entities (with device class: `motion`, `occupancy`, `presence`) are supported.

The presence state is published to a `binary_sensor` which will be named according to the area: `binary_sensor.area_presence_{area_name}`.

[Scenarios (Gherkin)](tests/features/presence.feature)

#### Presence lock

If only relying on motion sensors, presence could be cleared if there is only little or no movement. Presence lock can be used to treat an area as "occupied" regardless of sensor state.

A new switch with ID `switch.area_presence_lock_{area_name}` is created for each area. If the switch is `on`, lights will not be turned off.

[Scenarios (Gherkin)](tests/features/presence_lock.feature)

### Control lights automatically

Lights are automatically turned on and off based on presence in an area. By default a `lights.turn_on` command is issued for all lights as soon as presence is detected. Similarly `lights.turn_off` is ran as soon as presence is cleared in an area.

Note: this behaviour plays well together with extensions like for example [Adaptive Lighting](https://github.com/basnijholt/adaptive-lighting). If you wish to instead utilize scenes you may want to have a look at the following section.

[Scenarios (Gherkin)](tests/features/auto_lights.feature)

#### Scenes

By default, Auto Areas turns all lights on at 100% brightness. Additionally, this now supports user defined scenes by specifying a scene `entity_id` used for presence, goodbye, and/or sleeping modes. The sleeping mode scene is for when motion is detected during sleeping what should occur (for instance turning on very low level path lights).

One or more scenes can be configured, which overrides the default behavior of turning on/off all lights.

```yaml
auto_areas:
  bedroom:
    presence_scene: scene.bedroom_presence
    goodbye_scene: scene.bedroom_goodbye
    sleeping_scene: scene.bedroom_sleeping
```

#### Sleep mode

For areas marked as "sleeping area", automatic light control can be temporarily turned off. Lights are never turned on even if presence is detected.

A switch with ID `switch.auto_sleep_mode_{area_name}` is created for each sleeping area.
If the switch is turned `on`, automatic light control will be disabled and lights will stay off.

For information on how to configure this feature refer to the [configuration section](#configuration).

[Scenarios (Gherkin)](tests/features/sleep_mode.feature)

## Installation

Install as custom_component for HomeAssistant.

1. The recommended installation method is using [HACS](https://hacs.xyz). Add a new [custom repository](https://hacs.xyz/docs/faq/custom_repositories) for `https://github.com/c-st/auto_areas`. Then install it.
   Alternatively copy the folder `custom_components/auto_areas` to the `custom_components` folder of your Home Assistant installation.
2. Add an entry in `configuration.yaml`:

```yaml
auto_areas:
```

Entities are auto-discovered based on the areas they're assigned to. To customize the behaviour of areas have a look at [Configuration](#configuration).

## Configuration

The behaviour of areas can be customised by adding additional configuration in YAML.

Using the (normalised) name of the area as key, additional options can be enabled. In the following example the area with name `bedroom` is marked as sleeping area:

```yaml
# configuration.yaml

auto_areas:
  bedroom:
    is_sleeping_area: true
```

| Area option        | Description                                                                                         | Default value      |
| ------------------ | :-------------------------------------------------------------------------------------------------- | ------------------ |
| `is_sleeping_area` | Mark area as sleeping area. A switch for controlling sleep mode is created. [See more](#sleep-mode) | `false` (disabled) |
| `presence_scene`   | Scene to activate when presence is detected (when not sleeping)                                     | `None`             |
| `goodbye_scene`    | Scene to activate when presence is no longer detected                                               | `None`             |
| `sleeping_scene`   | Scene to activate when presence is detected and sleeping mode is on                                 | `None`             |

Created entities:

| Name                                      | Description                                                                     |
| ----------------------------------------- | :------------------------------------------------------------------------------ |
| `binary_sensor.area_presence_{area_name}` | Indicates whether area is currently considered occupied or not.                 |
| `switch.area_presence_lock_{area_name}`   | Created for all areas. If enabled, area presence is always on.                  |
| `switch.area_sleep_mode_{area_name}`      | Only created for sleeping areas. If enabled, light in sleeping areas stays off. |

## Development

Install dependencies:
`pip install --disable-pip-version-check -r requirements_test.txt`

Run tests:
`pytest`

Using [DevContainer](https://code.visualstudio.com/docs/remote/containers) is recommended (see config in `.devcontainer`).

## Acknowledgements

Auto Areas is inspired by [Magic Areas](https://github.com/jseidl/hass-magic_areas). I created this component to have something more tailored to my use-cases.
