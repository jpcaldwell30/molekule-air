import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
)
from .entity import MolekuleBaseEntity
_LOGGER: logging.Logger = logging.getLogger(__package__)

def add_space_before_capital(text):
    """Add a space before the first capital letter of a word."""
    new_string = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    new_string = new_string.title()
    return new_string

@dataclass(frozen=True, kw_only=True)
class MolekuleEntityDescription(SensorEntityDescription):
    """Describes Molekule sensor entity."""
    value: Callable[[dict], float | int | None]


SENSOR_TYPES: list[MolekuleEntityDescription] = [
    MolekuleEntityDescription(
        key="pecoFilter",
        translation_key="peco_filter",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data.get("pecoFilter"),
    ),
    MolekuleEntityDescription(
        key="fanspeed",
        translation_key="fan_speed",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data.get("fanspeed"),
    ),
    MolekuleEntityDescription(
        key="mode",
        value=lambda data: data.get("mode"),
    ),
    MolekuleEntityDescription(
        key="online",
        value=lambda data: data.get("online"),
    ),
    MolekuleEntityDescription(
        key="aqi",
        value=lambda data: data.get("aqi"),
    ),
    # Add more sensor types here
]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities based on a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_entities: list[MolekuleSensor] = []
    device_data = coordinator.data["content"]
    #_LOGGER.debug("device Data %s", device_data)
    for device in device_data:
        #_LOGGER.debug("device from sensor: %s", json.dumps(device))
        for description in SENSOR_TYPES:
            if description.key in device:
                    device_entities.append(
                        MolekuleSensor(
                            device,
                            coordinator,
                            config_entry,
                            description
                        )
                    )
    async_add_entities(device_entities)

class MolekuleSensor(MolekuleBaseEntity, SensorEntity):
    """Representation of a Molekule Sensor."""
    _attr_has_entity_name = True

    def __init__(
        self,
        device: dict[str, str],
        coordinator: CoordinatorEntity,
        entry: ConfigEntry,
        description: MolekuleEntityDescription,
    ) -> None:
        """Initialize a single sensor."""
        super().__init__(device, coordinator, entry)
        #_LOGGER.debug("adding sensor for device: %s with serial number: %s and description key: %s", device.get("name", "Molekule Device") , device_data.get("serialNumber"), description.key)
        self.entity_description: MolekuleEntityDescription = description
        self._attr_native_value = None
        self._attr_name = None
        device_id = f"{self.serial_nr}_{self.entity_description.key}"
        self._attr_unique_id = device_id #sensor unique id (not sensor device id)
        if self.entity_description.key == "aqi":
            sensor_name = "AQI"
        else:
            sensor_name = add_space_before_capital(self.entity_description.key)
        self._attr_name = sensor_name #sensor name?
        if description.key in device: #change this to make sure the device id matches for the sensor?
            value = description.value(device)
            if isinstance(value, (float, int)):
                self._attr_native_value = value #sensor value
            else:
                self._attr_native_value = value.capitalize()
        else:
            _LOGGER.debug("coordinator.data['content'] not found")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if "content" in self.coordinator.data:
            for device_data in self.coordinator.data["content"]:
                # _LOGGER.debug("data[serialNumber] %s", device_data["serialNumber"])
                # _LOGGER.debug("self.serial_nr %s", self.serial_nr)
                if device_data["serialNumber"] == self.serial_nr:
                    value = self.entity_description.value(device_data)
                    if isinstance(value, (float, int)):
                        self._attr_native_value = value #sensor value
                    else:
                        self._attr_native_value = value.capitalize()
                    self.async_write_ha_state()
                    break