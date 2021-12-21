# Auto Areas

A custom_component for Home Assistant for automatically setting up area-based automations.

Features:

- Auto-discovery based on area config. No configuration necessary.
- Turns lights on/off based on presence in an area.

## Configuration

Install in your custom_components folder (for example using HACS). Enable this component in your Home Assistant `configuration.yaml`:

```yaml
auto_areas:
```

## Development

Install dependencies:
`pip install -r requirements_test.txt`

Run tests:
`pytest`

Note: this component uses [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) to make testing easier.
