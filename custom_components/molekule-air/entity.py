from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from .properties import Model, Mode, Speed
from .api import MolekuleApiClient
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .const import CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MODELS = {
    Model.Molekule_Pro: "Molekule Pro",
    Model.Molekule_Mini_Plus: "Molekule Mini+",
    #None: None,
}

# from homeassistant.helpers import entity_registry as er, device_registry as dr

# entity_id = "sensor.foobar"

# entity_reg = er.async_get(hass)
# entry = entity_reg.async_get(entity_id)

# dev_reg = dr.async_get(hass)
# device = dev_reg.async_get(entry.device_id)

class MolekuleBaseEntity(CoordinatorEntity):
    """Base class for Rabbit Air entity."""

    def __init__(
        self,
        device: dict[str, str],
        coordinator: CoordinatorEntity,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        #_LOGGER.debug("data from base entity: %s", json.dumps(data))
        self.entry = entry
        self.serial_nr = device.get("serialNumber")
        self._attr_unique_id = f"{self.serial_nr}_molekule_purifier" #sensor/fan unique id (not sensor device id)
        #_LOGGER.debug("self.serial_nr %s", self.serial_nr)
        if not device.get("name", "Molekule Device").lower().startswith("molekule"):
            device_name = f"Molekule {device.get("name", "Molekule Device")}"
        else:
            device_name = device.get("name", "Molekule Device")
        self._attr_name =  device_name.title()
        if not device.get('subProduct', {}).get('name').lower().startswith("molekule"):
            device_unique_id = f"molekule_{device.get('subProduct', {}).get('name')}"
            device_unique_id = device_unique_id.replace(" ", "_")
        else:
            device_unique_id = device.get('subProduct', {}).get('name')
            device_unique_id = device_unique_id.replace(" ", "_")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_unique_id)},
            manufacturer="Molekule",
            model=device.get("name", "Molekule Device").title(),
            name=device_name,
            sw_version=device.get("firmwareVersion", "Unknown software version"),
        )

    # def _is_model(self, model: Model | list[Model]) -> bool:
    #     """Check the model of the device."""
    #     if isinstance(model, list):
    #         return self.data.model in model
    #     return self.data.model is model

    async def _set_state(self,
        data: dict[str, Any]
        ) -> None:
        """Change the state of the device."""
        _LOGGER.debug("set_state data: %s", data)
        user_input = self.entry.data
        username = user_input.get(CONF_USERNAME)
        password = user_input.get(CONF_PASSWORD)
        session = async_create_clientsession(self.hass)
        client = MolekuleApiClient(self.hass, username, password, session)
        if await client.async_verify_auth():
            await client.async_set_data(device_serial=self.serial_nr, data=data)
        await self.coordinator.async_request_refresh()

    #     self._async_handle_existing_entity()

    # async def _async_handle_existing_entity(self):
    #     """Update existing entity or create a new one."""
    #     entity_registry = await er.async_get(self.hass)

    #     if self.entity_id in entity_registry.entities:
    #         # Update the existing entity
    #         _LOGGER.debug("Updating existing entity: %s", self.entity_id)
    #         entry = entity_registry.async_get(self.entity_id)
    #         entry.unique_id = self.unique_id
    #         entity_registry.async_update_entity(entry)
    #     else:
    #         # Add a new entity
    #         self.hass.data[DOMAIN][self._platform].append(self)

    # @property
    # def unique_id(self): #device unique id
    #     """Return a unique ID to use for this entity."""
    #     if not self.coordinator.data["content"].get('subProduct', {}).get('name').lower().startswith("molekule"):
    #         unique_id = f"molekule_{self.coordinator.data["content"].get('subProduct', {}).get('name')}"
    #         unique_id = unique_id.replace(" ", "_")
    #     else:
    #         unique_id = self.coordinator.data["content"].get('subProduct', {}).get('name')
    #     #change this to change the device id:  self._device_data.get("name", "Molekule Device")? or f"Molekule {device_data.get('subProduct', {}).get('name')}"
    #     return unique_id
