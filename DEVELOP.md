# Develop

## Devcontainer

## Run component in HA

```
./scripts/develop
```

Open extension [in browser](http://localhost:8123/) and set up a new user.

##  Translations

https://developers.home-assistant.io/docs/internationalization/core/#config--options

## Testing

```
pytest

```

## configuration.yaml

```yaml
logger:
  default: info
  logs:
    custom_components.auto_areas: debug

# https://www.home-assistant.io/integrations/demo/
light:
  - platform: demo

binary_sensor:
  - platform: demo
```
