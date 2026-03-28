"""Sensor platform for Molekule Air."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import MolekuleBaseEntity


def add_space_before_capital(text: str) -> str:
    """Convert camelCase keys into a readable title."""
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", text).title()


def format_sensor_value(value: Any) -> str | int | float | None:
    """Normalize Molekule API values into sensor-friendly state values."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "Online" if value else "Offline"
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value.capitalize()
    return str(value)


@dataclass(frozen=True, kw_only=True)
class MolekuleEntityDescription(SensorEntityDescription):
    """Describes a Molekule sensor entity."""

    value: Callable[[dict[str, Any]], Any]


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
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Molekule sensors for a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[MolekuleSensor] = []

    for device in coordinator.data.get("content", []):
        for description in SENSOR_TYPES:
            if description.key in device:
                entities.append(
                    MolekuleSensor(device, coordinator, config_entry, description)
                )

    async_add_entities(entities)


class MolekuleSensor(MolekuleBaseEntity, SensorEntity):
    """Representation of a Molekule sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: dict[str, Any],
        coordinator,
        entry: ConfigEntry,
        description: MolekuleEntityDescription,
    ) -> None:
        super().__init__(device, coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self.serial_nr}_{description.key}"
        self._attr_name = (
            "AQI"
            if description.key == "aqi"
            else add_space_before_capital(description.key)
        )
        self._update_from_device(device)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device_data = self._get_device_data()
        if device_data is not None:
            self._update_from_device(device_data)
        super()._handle_coordinator_update()

    def _update_from_device(self, device: dict[str, Any]) -> None:
        """Update the native value from a device payload."""
        self._attr_native_value = format_sensor_value(
            self.entity_description.value(device)
        )
