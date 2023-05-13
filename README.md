# 🤖 Auto Areas

> _A custom component for [Home Assistant](https://www.home-assistant.io) which **automates** your **areas**._

An **area** in Home Assistant can represent a room or any other part of your home. Relevant entities and devices can be assigned to these areas; making it possible to create certain kind of automations **automatically**.

Example setup of areas and entities:

```md
- Area: Living room
  - Motion sensor
  - Motion sensor 2
  - Light
  - Light 2
  - Light 3
- Area: Bedroom
  - Motion sensor
  - Light
- Area: Office
  - Motion sensor
  - Light
- Area: Kitchen
  - Motion sensor
  - Light
```

Desired behaviour:

- if there is one or more motion sensors assigned to a room, all of them are used to determine if the room is currently occupied
- the lights in this room should be turned on if presence is detected
- once no presence is detected anymore, the lights should turn off again

To achieve this, without this component, it would be necessary to set up [automations](https://www.home-assistant.io/docs/automation/) for all sensors and lights for each of the areas.

---

For information on how to install this component see [Installation](#installation).

## Features

See how 🤖 **Auto Areas** can take over some of this work:

### Aggregated presence detection

Tracks the state of multiple sensor entities (for example motion sensors) to detect area presence.
It aggregates presence based on these rules:

- An area is considered "occupied" if there is at least one sensor in state `on` (for example motion is detected)
- Only if all sensors are `off` the area presence is cleared and the area is considered empty

Currently `binary_sensor` entities with device class: `motion`, `occupancy`, `presence` are supported.

The presence state is published to a single `binary_sensor` which will be named according to the area: `binary_sensor.area_presence_{area_name}`.

#### Presence lock

If only relying on motion sensors, presence could be cleared if there is only little or no movement. Presence lock can be used to treat an area as "occupied" regardless of sensor state.

A new switch with ID `switch.area_presence_lock_{area_name}` is created for each area. If the switch is `on`, lights will not be turned off.

### Control lights automatically

Lights are automatically turned on and off based on presence in an area.

#### Sleep mode

For areas marked as "sleeping area", automatic light control can be temporarily turned off. Lights are never turned on even if presence is detected.

A switch with ID `switch.area_sleep_mode_{area_name}` is created for each sleeping area. If the switch is turned `on`, automatic light control will be disabled and lights will stay off.

For information on how to mark an area as "sleeping area" refer to the [configuration section](#configuration).

## Installation

Auto Areas is a custom_component for Home Assistant.

1. The recommended installation method is using [HACS](https://hacs.xyz): search for "Auto Areas", install it and restart Home Assistant.
Alternatively [download a release](https://github.com/c-st/auto_areas/releases) and copy the folder `custom_components/auto_areas` to the `custom_components` folder of your Home Assistant installation.
2. For each area that you want to control with Auto Areas, go to "Settings"/"Devices & Services"/"Add integration" and search for "Auto Areas". You can then create an instance for each area you want to manage.

## Configuration

Navigate to "Settings"/"Devices & Services"/"Auto Areas" and select the area for which you want to change the options for. Select "Configure" and change the behaviour with the following options:

| Area option        | Description                                                                                         | Default value      |
| ------------------ | :-------------------------------------------------------------------------------------------------- | ------------------ |
| Set as sleeping area | Mark area as sleeping area. A switch for controlling sleep mode is created. [See more](#sleep-mode) | `false` (disabled) |

## Development

Using [DevContainer](https://code.visualstudio.com/docs/remote/containers) is recommended (see config in `.devcontainer`).
