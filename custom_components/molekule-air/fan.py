"""Molekule Air Purifier Device."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
import logging
from typing import Any, Optional, Union

import voluptuous as vol

from homeassistant.components.fan import DOMAIN, FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import (
    ATTR_AIRFLOW,
    #ATTR_FILTER_REPLACEMENT_DATE,
    #ATTR_LOCATION,
    ATTR_POWER,
    ORDERED_NAMED_FAN_SPEEDS,
    PRESET_MODE_SMART,
    #PRESET_MODE_AUTO_PLASMA_OFF,
    PRESET_MODE_MANUAL,
    #PRESET_MODE_MANUAL_PLASMA_OFF,
    #PRESET_MODE_SLEEP,
    PRESET_MODES,
    #SERVICES,
    MOLEKULE_DATA_COORDINATOR,
    MOLEKULE_DATA_KEY,
    MOLEKULE_DOMAIN,
)
from .device_wrapper import MolekuleDeviceWrapper
from .manager import MolekuleEntity, MolekuleManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Molekule air purifiers."""
    data = hass.data[MOLEKULE_DOMAIN][entry.entry_id]
    manager: MolekuleManager = data[MOLEKULE_DATA_COORDINATOR]
    entities = [
        MolekulePurifier(wrapper, manager) for wrapper in manager.get_device_wrappers()
    ]
    data[MOLEKULE_DATA_KEY] = entities
    async_add_entities(entities)

    async def async_service_handler(service_call):
        """Service handler."""
        method = "async_" + service_call.service
        _LOGGER.debug("Service '%s' invoked", service_call.service)

        # The defined services do not accept any additional parameters
        params = {}

        entity_ids = service_call.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                entity
                for entity in data[MOLEKULE_DATA_KEY]
                if entity.entity_id in entity_ids
            ]
        else:
            devices = data[MOLEKULE_DATA_KEY]

        state_update_tasks = []
        for device in devices:
            if not hasattr(device, method):
                continue

            await getattr(device, method)(**params)
            state_update_tasks.append(asyncio.create_task(device.async_update_ha_state(True)))

        if state_update_tasks:
            # Update device states in HA
            await asyncio.wait(state_update_tasks)

    # for service in SERVICES:
    #     hass.services.async_register(
    #         MOLEKULE_DOMAIN,
    #         service,
    #         async_service_handler,
    #         schema=vol.Schema({ATTR_ENTITY_ID: cv.entity_ids}),
    #     )

    _LOGGER.info("Added %s Molekule fans", len(entities))


class MolekulePurifier(MolekuleEntity, FanEntity):
    """Representation of a Molekule Purifier entity."""

    # https://developers.home-assistant.io/docs/core/entity/fan/
    _attr_supported_features = FanEntityFeature.PRESET_MODE | FanEntityFeature.SET_SPEED

    def __init__(self, wrapper: MolekuleDeviceWrapper, coordinator: MolekuleManager) -> None:
        """Initialize the entity."""
        super().__init__(wrapper, coordinator)
        self._attr_unique_id = f"{DOMAIN}.{MOLEKULE_DOMAIN}_{self._mac}"

    @property
    def name(self) -> Union[str, None]:
        """Entity Name.

        Returning None, since this is the primary entity.
        """
        return None

    @property
    def extra_state_attributes(self) -> Union[Mapping[str, Any], None]:
        """Return the state attributes."""
        attributes = {}
        state = self._wrapper.get_state()

        if state is not None:
            for key, value in state.items():
                # The power attribute is the entity state, so skip it
                if key != ATTR_POWER:
                    attributes[key] = value

        return attributes

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._wrapper.is_on

    @property
    def percentage(self) -> Union[int, None]:
        """Return the current speed percentage."""
        state = self._wrapper.get_state()
        if state is None:
            return None
        if self._wrapper.is_smart:
            return None
        if state.get(ATTR_AIRFLOW) is None:
            return None

        return ordered_list_item_to_percentage(
            ORDERED_NAMED_FAN_SPEEDS, state.get(ATTR_AIRFLOW)
        )

    @property
    def preset_mode(self) -> Union[str, None]:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        state = self._wrapper.get_state()
        if state is None:
            return None
        if self._wrapper.is_smart:
            return (
                PRESET_MODE_SMART
            )
        if self._wrapper.is_manual:
            return (
                PRESET_MODE_MANUAL
            )

        return None

    @property
    def preset_modes(self) -> Union[list[str], None]:
        """Return a list of available preset modes."""
        return PRESET_MODES

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return ORDERED_NAMED_FAN_SPEEDS

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            await self._wrapper.async_set_speed(
                percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
            )

        self.async_write_ha_state()

    async def async_turn_on(
        self,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=unused-argument
        """Turn on the purifier."""

        if percentage:
            await self.async_set_percentage(percentage)
        if preset_mode:
            await self._wrapper.async_set_preset_mode(preset_mode)
        else:
            await self._wrapper.async_turn_on()

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the purifier."""
        await self._wrapper.async_turn_off()
        self.async_write_ha_state()

    # async def async_plasmawave_on(self) -> None:
    #     """Turn on plasma wave."""
    #     await self._wrapper.async_plasmawave_on()
    #     self.async_write_ha_state()

    # async def async_plasmawave_off(self) -> None:
    #     """Turn off plasma wave."""
    #     await self._wrapper.async_plasmawave_off()
    #     self.async_write_ha_state()

    # async def async_plasmawave_toggle(self) -> None:
    #     """Toggle plasma wave."""

    #     if self._wrapper.is_plasma_on:
    #         await self._wrapper.async_plasmawave_off()
    #     else:
    #         await self._wrapper.async_plasmawave_on()

    #     self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await self._wrapper.async_set_preset_mode(preset_mode)
        self.async_write_ha_state()