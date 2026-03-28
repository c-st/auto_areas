# 🤖 Auto Areas

> _A custom component for [Home Assistant](https://www.home-assistant.io) which **automates** your **areas**._

An **area** in Home Assistant can represent a room or any other part of your home. Relevant entities and devices can be assigned to these areas; making it possible to create certain kind of automations **automatically**.

Example setup of areas and entities:

```md
- Living room (Area)
  - Motion sensor
  - Motion sensor 2
  - Illuminance sensor
  - Light
  - Light 2
  - Light 3
  - Cover 1
  - Cover 2
  - Cover 3
- Bedroom (Area)
  - Motion sensor
  - Illuminance sensor
  - Light
  - Cover 1
  - Cover 2
- Office (Area)
  - Motion sensor
  - Light
- Kitchen (Area)
  - Motion sensor
  - Light
```

Desired behaviour:

- if there is one or more motion sensors assigned to a room, all of them are used to determine if the room is currently occupied
- the lights in this room should be turned on if presence is detected
- additionally the lights should only be turned on if it's sufficiently dark in the area
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

#### Presence timeout

When relying on motion sensors, presence can be cleared if you sit still long enough that motion sensors stop firing. To prevent lights turning off prematurely, you can configure a **presence timeout** (in seconds) per area.

When set (value > 0):
- Presence goes **on immediately** when any sensor triggers
- Presence goes **off only after the configured delay** with no new sensor activity
- If a sensor triggers again during the delay, the timer **resets**
- When timeout = 0 (default), behaviour is unchanged — presence clears immediately

Configure this in the options flow for each area under "Presence timeout".

#### Presence lock

If only relying on motion sensors, presence could be cleared if there is only little or no movement. Presence lock can be used to treat an area as "occupied" regardless of sensor state.

A new switch with ID `switch.area_presence_lock_{area_name}` is created for each area. If the switch is `on`, lights will not be turned off.

### Environmental Safety

Aggregates safety-related binary sensors within each area into a single `binary_sensor.area_safety_{area_name}` entity. If **any** safety sensor in the area is triggered, the aggregate is `on` (alert active). When all sensors are `off` (or no safety sensors are present), the aggregate is `off`.

Supported `binary_sensor` device classes:

- `smoke` — smoke detectors
- `co` — carbon monoxide detectors
- `gas` — gas leak detectors
- `moisture` — water/leak detectors
- `heat` — heat sensors (fire-related)
- `safety` — generic safety sensors

The sensor uses **OR** logic and **fails safe**: when no safety sensors are assigned to an area, the aggregate reports `off`.

**Example use cases:**

- Send a push notification when any safety sensor triggers in the house
- Trigger a siren or alarm automation when smoke or CO is detected in any room
- Create a dashboard card showing per-area safety status

### Area Open

Aggregates contact/opening binary sensors within each area into a single `binary_sensor.area_open_{area_name}` entity. If **any** door, window, or opening sensor in the area is open, the aggregate is `on`. When all sensors are closed (or no relevant sensors are present), the aggregate is `off`.

Supported `binary_sensor` device classes:

- `door` — door contact sensors
- `window` — window contact sensors
- `opening` — generic opening sensors
- `garage_door` — garage door sensors
- `lock` — locks (unlocked = on/open, locked = off/closed)

The sensor uses **OR** logic and **fails safe**: when no open/closed sensors are assigned to an area, the aggregate reports `off`.

**Example use cases:**

- Alert when a window is left open while you are away
- Dashboard card showing which areas have open doors or windows
- Automation to turn off HVAC when a window is open in a room

### Control lights automatically

Lights are automatically turned on and off based on presence in an area.

By default all light entities of an area are managed. A list of entities to be ignored can be defined in the configuration options.

#### Illuminance threshold

You can configure a minimum illuminance threshold per area. When set:

- **On entry:** If the area is already bright enough (above threshold), lights will not turn on automatically.
- **While present:** If illuminance drops below the threshold and lights were not previously turned on by Auto Areas, lights will turn on automatically.
- **Manual override:** If Auto Areas turned on the lights due to low illuminance and you then manually turn them off, they will stay off — even if illuminance drops further. This override resets when you leave the area or turn the lights back on.

#### Sleep mode

For areas marked as "sleeping area", automatic light control can be temporarily turned off. Lights are never turned on even if presence is detected.

A switch with ID `switch.area_sleep_mode_{area_name}` is created for each sleeping area. If the switch is turned `on`, automatic light control will be disabled and lights will stay off.

For information on how to mark an area as "sleeping area" refer to the [configuration section](#configuration).

### Aggregated sensor readings

#### Aggregated illuminance

Tracks all illuminance measuring sensors in an area. By default the last known illuminance of all sensors is used.
This illuminance is published in a `sensor` with the ID `sensor.area_illuminance_{area_name}`.

#### Aggregated temperature

Tracks all temperature measuring sensors in an area. By default the average of known temperature of all sensors is used.
This temperature is published in a `sensor` with the ID `sensor.area_temperature_{area_name}`.

#### Aggregated humidity

Tracks all humidity measuring sensors in an area. By default the maximum of known humidity of all sensors is used.
This humidity is published in a `sensor` with the ID `sensor.area_humidity_{area_name}`.

#### Calculation methods

- `mean` - The arithmetic mean of all sensor states that are available and have a numeric value.
- `median` - The arithmetic median of all sensor states that are available and have a numeric value.
- `min` - The minimum of all sensor states that are available and have a numeric value.
- `max` - The maximum of all sensor states that are available and have a numeric value.
- `last` - The last updated of all sensor states that is available and has a numeric value.

### Automatic groups

#### Cover groups

If at least one cover is detected in an area, a cover group is created. This group can be used to control all blinds at once.

#### Light groups

If an area contains at least one light, a group is created. This group can be used to control all lights at once.

## Installation

Auto Areas is a custom_component for Home Assistant.

1. The recommended installation method is using [HACS](https://hacs.xyz): search for "Auto Areas", install it and restart Home Assistant.
   Alternatively [download a release](https://github.com/c-st/auto_areas/releases) and copy the folder `custom_components/auto_areas` to the `custom_components` folder of your Home Assistant installation.
2. For each area that you want to control with Auto Areas, go to "Settings"/"Devices & Services"/"Add integration" and search for "Auto Areas". You can then create an instance for each area you want to manage.

## Configuration

Navigate to "Settings"/"Devices & Services"/"Auto Areas" and select the area for which you want to change the options for. Select "Configure" and change the behaviour with the following options:

| Area option             | Description                                                                                                                  | Default value      |
| ----------------------- | :--------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Set as sleeping area    | Mark area as sleeping area. A switch for controlling sleep mode is created. [See more](#sleep-mode).                         | `false` (disabled) |
| Presence timeout        | Delay (in seconds) before clearing presence after all sensors go off. Prevents lights turning off when sitting still. [See more](#presence-timeout). | `0` (disabled)     |
| Excluded light entities | Entities to exclude from automatic light control. These lights are never turned on or off and are not part of a light group. | `[]` (none)        |
| Illuminance threshold   | Only if area illuminance is lower than this threshold, lights are turned on.                                                 | `0`                |
| Illuminance calculation | Configure the calculation for the aggregate illuminance sensor.                                                              | `last`             |
| Temperature calculation | Configure the calculation for the aggregate temperature sensor.                                                              | `mean`             |
| Humditity calculation   | Configure the calculation for the aggregate humidity sensor.                                                                 | `max`              |

## Development

Using [DevContainer](https://code.visualstudio.com/docs/remote/containers) is recommended (see config in `.devcontainer`).
