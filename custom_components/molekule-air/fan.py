"""Support for Rabbit Air fan entity."""

from __future__ import annotations

import ast
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN
from .entity import MolekuleBaseEntity
from .properties import Speed, Mode

_LOGGER: logging.Logger = logging.getLogger(__package__)

SPEED_LIST = [
    Speed.Silent.value,
    Speed.Low.value,
    Speed.Medium.value,
    Speed.High.value,
    Speed.Turbo.value,
    Speed.SuperTurbo.value
]

PRESET_MODE_AUTO = "auto"
PRESET_MODE_MANUAL = "manual"

PRESET_MODES = {
    PRESET_MODE_AUTO: Mode.auto.name,
    PRESET_MODE_MANUAL: Mode.manual.name,
}

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_entities: list[MolekuleFanEntity] = []
    device_data = coordinator.data["content"]
    for device in device_data:
        #_LOGGER.debug("device in fan setup %s", device)
        device_entities.append(
            MolekuleFanEntity(
                device,
                coordinator,
                config_entry
            )
        )
    async_add_entities(device_entities)

class MolekuleFanEntity(MolekuleBaseEntity, FanEntity):
    """Fan control functions of the Rabbit Air air purifier."""

    _attr_supported_features = FanEntityFeature.PRESET_MODE | FanEntityFeature.SET_SPEED

    def __init__(
        self,
        device: dict[str, str],
        coordinator: CoordinatorEntity,
        entry: ConfigEntry
    ) -> None:
        """Initialize the entity."""
        super().__init__(device, coordinator, entry)
        self._attr_preset_modes = list(PRESET_MODES)
        # if self._is_model(Model.MinusA2):
        #     self._attr_preset_modes = list(PRESET_MODES)
        # elif self._is_model(Model.A3):
        #     # A3 does not support Pollen mode
        #     self._attr_preset_modes = [
        #         k for k in PRESET_MODES if k != PRESET_MODE_POLLEN
        #     ]
        self._attr_speed_count = len(SPEED_LIST)

        self._get_state_from_coordinator_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._get_state_from_coordinator_data()
        super()._handle_coordinator_update()

    def _get_state_from_coordinator_data(self) -> None:
        """Populate the entity fields with values from the coordinator data."""
        if "content" in self.coordinator.data:
            for data in self.coordinator.data["content"]:
                if data["serialNumber"] == self.serial_nr:
                    if data.get("mode") == "off" or data.get("mode") is None:
                        self._attr_percentage = 0
                    elif data.get("fanspeed") is None:
                        self._attr_percentage = None
                    else:
                        self._attr_percentage = ordered_list_item_to_percentage(
                            SPEED_LIST, ast.literal_eval(data.get("fanspeed"))
                        )
                    # Preset mode
                    if data.get("mode") == "off" or data.get("mode") is None:
                        self._attr_preset_mode = None
                    else:
                        # Get key by value in dictionary
                        if "mode" in data and data["mode"] in PRESET_MODES.values():
                            self._attr_preset_mode = next(
                                k for k, v in PRESET_MODES.items() if v == data.get("mode")
                            )

    async def async_set_preset_mode(self, preset_mode: str) -> None: #not implemented yet
        """Set new preset mode."""
        data = {"power":"on",
                "mode":preset_mode
                }
        _LOGGER.debug("data from preset mode is: %s", data)
        await self._set_state(data)
        self._attr_preset_mode = preset_mode
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        if percentage > 0:
            value = percentage_to_ordered_list_item(SPEED_LIST, percentage)
            data = {"power":"on",
                    "speed":value
                    }
            await self._set_state(data)
            self._attr_percentage = percentage
        else:
            data = {"power":"off"}
            await self._set_state(data)
            self._attr_percentage = 0
            self._attr_preset_mode = None
        self.async_write_ha_state()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        data = {"power":"on"}
        mode_value: Mode | None = None
        if preset_mode is not None:
            mode_value = PRESET_MODES[preset_mode]
            data["mode"] = mode_value
        speed_value: Speed | None = None
        if percentage is not None:
            speed_value = percentage_to_ordered_list_item(SPEED_LIST, percentage)
            data["speed"] = speed_value
        _LOGGER.debug("aync_turn on data: %s", data)
        await self._set_state(data)
        if percentage is not None:
            self._attr_percentage = percentage
        if preset_mode is not None:
            self._attr_preset_mode = preset_mode
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        data = {"power":"off"}
        await self._set_state(data)
        self._attr_percentage = 0
        self._attr_preset_mode = None
        self.async_write_ha_state()
