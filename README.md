# Auto Areas

A custom component for [Home Assistant](https://www.home-assistant.io) for automatically setting up area-based automations.

Having your devices structured by areas (for example per room) makes it easy to create certain kind of automations automatically.

_Light control based on presence in your rooms_:
In most of the cases you want the lights in a room to be turned on when presence is detected.
Likewise you want the lights to turn off as soon as the occupancy is cleared.
Also you only want the lights to turn on if it is necessary (for example based on measured illuminance or when you're not sleeping).

Auto Areas gathers relevant entities from each area. It then keeps track of the state of multiple presence sensors (`binary_sensor`). Measurement values for `temperature`, `humidity`, `illuminance` from multiple devices are aggregated per area.

Domains:

- binary_sensor (`motion`, `occupancy`, `presence`)
- light
- switch
- sensor

Features:

- Detect presence in an area based on multiple sensors
- Automatically turn lights on/off based on presence in an area
- ...

## Configuration

Install in your custom_components folder (for example using [HACS](https://hacs.xyz)). Enable this component in your Home Assistant `configuration.yaml`:

```yaml
auto_areas:
```

Entities are auto-discovered based on the area they're assigned to in Home Assistant.

## Features

### Presence detection

- [ ] Create a `binary_sensor` indicating presence detected for each area
- [ ] Create a `switch`. If on, presence should be assumed even when sensors disagree ("presence lock", "presence hold"). Reset automatically?
- [ ] Support `media_player` domain. (What about others - door?)

### Control lights automatically

- [ ] Create switch for sleep mode

## Development

Install dependencies:
`pip install --disable-pip-version-check -r requirements_test.txt`

Run tests:
`pytest`

Note: this component uses [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) to make testing easier.

_Note_:
This project is heavily inspired by the custom component [Magic Areas](https://github.com/jseidl/hass-magic_areas).
