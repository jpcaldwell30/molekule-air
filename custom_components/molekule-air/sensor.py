"""Molekule Air Purfier Air QValue Sensor."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, Final, Union

from homeassistant.components.sensor import (
    DOMAIN,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import MOLEKULE_DOMAIN
from .const import (
    ATTR_AIR_AQI,
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    SENSOR_AIR_QVALUE,
    SENSOR_AQI,
    SENSOR_FILTER_LIFE,
    MOLEKULE_DATA_COORDINATOR,
)
from .device_wrapper import MolekuleDeviceWrapper
from .manager import MolekuleEntity, MolekuleManager

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_FILTER_LIFE,
        icon="mdi:air-filter",
        name="Filter Life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_AQI,
        icon="mdi:blur",
        name="AQI",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Molekule sensors."""
    data = hass.data[MOLEKULE_DOMAIN][entry.entry_id]
    manager: MolekuleManager = data[MOLEKULE_DATA_COORDINATOR]

    entities = [
        MolekuleSensor(wrapper, manager, description)
        for description in SENSOR_TYPES
        for wrapper in manager.get_device_wrappers()
    ]
    async_add_entities(entities)
    _LOGGER.info("Added %s sensors", len(entities))


class MolekuleSensor(MolekuleEntity, SensorEntity):
    """Representation of a Molekule Purifier sensor."""

    def __init__(
        self,
        wrapper: MolekuleDeviceWrapper,
        coordinator: MolekuleManager,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        self._attr_unique_id = (
            f"{DOMAIN}.{MOLEKULE_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def extra_state_attributes(self) -> Union[Mapping[str, Any], None]:
        """Return the state attributes."""

        attributes = None
        if self.entity_description.key == SENSOR_AIR_QVALUE:
            attributes = {ATTR_AIR_QUALITY: None}

            state = self._wrapper.get_state()
            if state is not None:
                attributes[ATTR_AIR_QUALITY] = state.get(ATTR_AIR_QUALITY)

        return attributes

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        state = self._wrapper.get_state()
        if state is None:
            return None

        if self.entity_description.key == SENSOR_AIR_QVALUE:
            return state.get(ATTR_AIR_QVALUE)

        if self.entity_description.key == SENSOR_AQI:
            return state.get(ATTR_AIR_AQI)

        if self.entity_description.key == SENSOR_FILTER_LIFE:
            value = state.get(SENSOR_FILTER_LIFE)
            if value is None:
                return None

        _LOGGER.error("Unhandled sensor '%s' encountered", self.entity_description.key)
        return None
