# Auto Areas

A custom component for [Home Assistant](https://www.home-assistant.io) which automates entities by area.

Having your devices structured by areas (for example per room) makes it easy to create certain kind of automations automatically.

For example controlling _lights in a room based on presence_:
In most of the cases you want the lights in a room to be turned on when presence is detected. Likewise you want the lights to turn off as soon as the occupancy is cleared. Also you only want the lights to turn on if it is necessary (for example based on measured illuminance or when you're not sleeping).

Normally it would be necessary to set up automations for each of the sensors, switches and lights (and also maintain them).

🤖 Auto Areas tries to take over some of this work: it gathers relevant entities from each area. It then keeps track of all presence sensors (`binary_sensor`) in each area. If presence is detected, it turns on all lights in the area. If no presence is reported anymore by any sensor in the area, the lights are turned off.

Domains:

- binary_sensor (`motion`, `occupancy`, `presence`)
- light
- switch
- sensor

Features:

- Detect presence in an area based on multiple sensors
- Automatically turn lights on/off based on presence in an area
- ...

## Features

### Presence detection

- [ ] Create a `binary_sensor` indicating presence detected for each area
- [ ] Create a `switch`. If on, presence should be assumed even when sensors disagree ("presence lock", "presence hold"). Reset automatically?
- [ ] Support `media_player` domain. (What about others - door?)

### Control lights automatically

- [ ] Create switch for sleep mode

### Aggregate sensor data

Measurement values for `temperature`, `humidity`, `illuminance` from multiple devices are aggregated per area.

## Configuration

Install in the custom_components folder of your Home Assistant installation (for example using [HACS](https://hacs.xyz)). Add an entry to `configuration.yaml`:

```yaml
auto_areas:
```

Entities are auto-discovered based on the area they're assigned to in Home Assistant.

## Development

Install dependencies:
`pip install --disable-pip-version-check -r requirements_test.txt`

Run tests:
`pytest`

_Note_:
This project is heavily inspired by [Magic Areas](https://github.com/jseidl/hass-magic_areas).
