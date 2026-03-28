"""Shared entity helpers for Molekule Air."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from . import MolekuleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class MolekuleBaseEntity(CoordinatorEntity["MolekuleDataUpdateCoordinator"]):
    """Base entity class for Molekule devices."""

    def __init__(
        self,
        device: dict[str, Any],
        coordinator: "MolekuleDataUpdateCoordinator",
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.serial_nr = device.get("serialNumber", "")

        product_name = device.get("subProduct", {}).get("name") or "Molekule Device"
        configured_name = device.get("name") or product_name
        if configured_name.lower().startswith("molekule"):
            device_name = configured_name
        else:
            device_name = f"Molekule {configured_name}"

        self._attr_name = device_name
        self._attr_unique_id = f"{self.serial_nr}_molekule_purifier"

        device_info: dict[str, Any] = {
            "identifiers": {(DOMAIN, self.serial_nr)},
            "manufacturer": "Molekule",
            "model": product_name,
            "name": device_name,
            "serial_number": self.serial_nr,
            "sw_version": device.get("firmwareVersion") or "Unknown software version",
        }

        mac_address = device.get("macAddress")
        if mac_address:
            device_info["connections"] = {
                (CONNECTION_NETWORK_MAC, mac_address.lower()),
            }

        self._attr_device_info = DeviceInfo(**device_info)

    async def _set_state(self, data: dict[str, Any]) -> None:
        """Apply a state change and refresh coordinator data."""
        _LOGGER.debug("Applying requested state for %s: %s", self.serial_nr, data)
        await self.coordinator.api.async_set_data(self.serial_nr, data)
        await self.coordinator.async_request_refresh()

    def _get_device_data(self) -> dict[str, Any] | None:
        """Return the latest coordinator payload for this device."""
        for device in self.coordinator.data.get("content", []):
            if device.get("serialNumber") == self.serial_nr:
                return device
        return None
