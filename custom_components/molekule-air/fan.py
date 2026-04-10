"""Fan platform for Molekule Air devices."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN, MODE_MANUAL, MODE_SMART, PRESET_MODES
from .entity import MolekuleBaseEntity
from .properties import Speed

_LOGGER = logging.getLogger(__name__)

SPEED_LIST = [speed.value for speed in Speed]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Molekule fan entities for a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MolekuleFanEntity(device, coordinator, config_entry)
            for device in coordinator.data.get("content", [])
        ]
    )


def _parse_speed(value: Any) -> int | None:
    """Parse a speed value from the Molekule payload."""
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class MolekuleFanEntity(MolekuleBaseEntity, FanEntity):
    """Representation of a Molekule air purifier as a fan."""

    _attr_supported_features = (
        FanEntityFeature.PRESET_MODE
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    def __init__(
        self,
        device: dict[str, Any],
        coordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(device, coordinator, entry)
        self._attr_preset_modes = PRESET_MODES.copy()
        self._attr_speed_count = len(SPEED_LIST)
        self._get_state_from_coordinator_data()

    @property
    def icon(self) -> str:
        """Return the icon for the Molekule fan."""
        return "mdi:air-purifier"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._get_state_from_coordinator_data()
        super()._handle_coordinator_update()

    def _get_state_from_coordinator_data(self) -> None:
        """Populate entity state from the latest coordinator data."""
        device_data = self._get_device_data()
        if device_data is None:
            return

        mode = device_data.get("mode")
        fan_speed = _parse_speed(device_data.get("fanspeed"))

        if mode in (None, "off"):
            self._attr_is_on = False
            self._attr_percentage = 0
            self._attr_preset_mode = None
            return

        self._attr_is_on = True
        self._attr_percentage = (
            ordered_list_item_to_percentage(SPEED_LIST, fan_speed)
            if fan_speed is not None
            else None
        )
        self._attr_preset_mode = mode if mode in PRESET_MODES else None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the Molekule operating mode."""
        if preset_mode not in PRESET_MODES:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

        await self._set_state({"power": "on", "mode": preset_mode})

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed as a percentage."""
        if percentage > 0:
            speed = percentage_to_ordered_list_item(SPEED_LIST, percentage)
            await self._set_state({"power": "on", "mode": MODE_MANUAL, "speed": speed})
            return

        await self._set_state({"power": "off"})

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        data: dict[str, Any] = {"power": "on"}

        if preset_mode is not None:
            if preset_mode not in PRESET_MODES:
                raise ValueError(f"Unsupported preset mode: {preset_mode}")
            data["mode"] = preset_mode

        if percentage is not None:
            data["mode"] = MODE_MANUAL
            data["speed"] = percentage_to_ordered_list_item(SPEED_LIST, percentage)

        await self._set_state(data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._set_state({"power": "off"})
