"""The Molekule Air Purifier component."""

from __future__ import annotations
import dataclasses
import aiohttp
import logging

logger = logging.getLogger(__name__)

from .const import (
    ATTR_AIRFLOW,
    ATTR_MODE,
    #ATTR_POWER,
    #MODE_AUTO,
    MODE_SMART,
    MODE_MANUAL,
    OFF_VALUE,
    #ON_VALUE,
    #EPRESET_MODE_AUTO,
    #PRESET_MODE_AUTO_PLASMA_OFF,
    #PRESET_MODE_MANUAL,
    #PRESET_MODE_SMART,
    #PRESET_MODE_MANUAL_PLASMA_OFF,
    #PRESET_MODE_SLEEP,
    PRESET_MODES,
    NumericPresetModes,
)

from .driver import MolekuleDriver

@dataclasses.dataclass
class MyMolekuleDeviceStub:
    """Molekule purifier device information."""

    serial: str  # pylint: disable=invalid-name
    mac: str
    alias: str
    model: str
    fw_version: str

class MolekuleDeviceWrapper:
    """Representation of the Molekule device data."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        client: aiohttp.ClientSession,
        device_stub: MyMolekuleDeviceStub,
        #logger,
    ) -> None:
        """Initialize the wrapper."""

        self._driver = MolekuleDriver(device_stub.serial, client)

        # Start as empty object in case fan was operated before it got updated
        self._state = {}

        self._on = False
        self._smart = False
        self._manual = False
        self._logger = logger

        self.device_stub = device_stub
        self._alias = device_stub.alias

    async def update(self) -> None:
        """Update the device data."""
        self._state = await self._driver.get_state()
        #self._auto = self._manual = self._sleep = self._plasma_on = False
        self._smart = self._manual = False

        self._on = self._state.get(ATTR_MODE) != OFF_VALUE
        #self._plasma_on = self._state.get(ATTR_PLASMA) == ON_VALUE

        # Sleep: airflow=sleep, mode can be manual
        # Auto: mode=auto, airflow can be anything
        # Low: manual+low

        # off: fan speed can be anything
        # smart: fan speed can be anything, silent can be 0/1
        # manual: fan speed can be 1-6
        
        if self._state.get(ATTR_MODE) == MODE_SMART:
            self._smart = True
            self._manual = False
        elif self._state.get(ATTR_MODE) == MODE_MANUAL:
            self._smart = False
            self._manual = True

        # if self._state.get(ATTR_MODE) == MODE_AUTO:
        #     self._auto = True
        #     self._manual = False
        # elif self._state.get(ATTR_MODE) == MODE_MANUAL:
        #     self._auto = False
        #     self._manual = True

        # if self._state.get(ATTR_AIRFLOW) == AIRFLOW_SLEEP:
        #     self._sleep = True
        self._logger.debug(
            #"%s: updated on=%s, auto=%s, manual=%s, sleep=%s, airflow=%s, plasma=%s",
            "%s: updated on=%s, smart=%s, manual=%s, airflow=%s",
            self._alias,
            self._on,
            self._smart,
            self._manual,
            # self._sleep,
            self._state.get(ATTR_AIRFLOW),
            # self._plasma_on,
        )

    def get_state(self) -> dict[str, str]:
        """Return the device data."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Return if the purifier is on."""
        return self._on

    @property
    def is_smart(self) -> bool:
        """Return if the purifier is in Auto mode."""
        return self._smart

    @property
    def is_manual(self) -> bool:
        """Return if the purifier is in Manual mode."""
        return self._manual

    # @property
    # def is_plasma_on(self) -> bool:
    #     """Return if plasma is on."""
    #     return self._plasma_on

    # @property
    # def is_sleep(self) -> bool:
    #     """Return if the purifier is in Sleep mode."""
    #     return self._sleep

    async def async_ensure_on(self) -> None:
        """Turn on the purifier."""
        if not self._on:
            self._on = True

            self._logger.debug("%s => turned on", self._alias)
            await self._driver.turn_on()

    async def async_turn_on(self) -> None:
        """Turn on the purifier in Auto mode."""
        await self.async_ensure_on()
        await self.async_smart()

    async def async_turn_off(self) -> None:
        """Turn off the purifier."""
        if self._on:
            self._on = False

            self._logger.debug("%s => turned off", self._alias)
            await self._driver.turn_off()

    async def async_smart(self) -> None:
        """Put the purifier in Smart mode with Low airflow.

        Plasma state is left unchanged. The Molekule server seems to sometimes
        turns it on for Smart mode.
        """

        if not self._smart:
            self._smart = True
            self._manual = False
            #self._sleep = False
            self._state[ATTR_MODE] = MODE_SMART
            # self._state[
            #     ATTR_AIRFLOW
            # ] = AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP
            self._logger.debug("%s => set mode=smart", self._alias)
            await self._driver.smart()

    # async def async_plasmawave_on(self, force: bool = False) -> None:
    #     """Turn on plasma wave."""

    #     if force or not self._plasma_on:
    #         self._plasma_on = True
    #         self._state[ATTR_PLASMA] = ON_VALUE

    #         self._logger.debug("%s => set plasmawave=on", self._alias)
    #         await self._driver.plasmawave_on()

    # async def async_plasmawave_off(self, force: bool = False) -> None:
    #     """Turn off plasma wave."""

    #     if force or self._plasma_on:
    #         self._plasma_on = False
    #         self._state[ATTR_PLASMA] = OFF_VALUE

    #         self._logger.debug("%s => set plasmawave=off", self._alias)
    #         await self._driver.plasmawave_off()

    async def async_manual(self) -> None:
        """Put the purifier in Manual mode """

        if not self._manual:
            self._manual = True
            self._smart = False
            # self._sleep = False
            self._state[ATTR_MODE] = MODE_MANUAL
            # self._state[
            #     ATTR_AIRFLOW
            # ] = AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP

            self._logger.debug("%s => set mode=manual", self._alias)
            await self._driver.manual()

    # async def async_sleep(self) -> None:
    #     """Turn the purifier in Manual mode with Sleep airflow. Plasma state is left unchanged."""

    #     if not self._sleep:
    #         self._sleep = True
    #         self._auto = False
    #         self._manual = False
    #         self._state[ATTR_AIRFLOW] = AIRFLOW_SLEEP
    #         self._state[ATTR_MODE] = MODE_MANUAL

    #         self._logger.debug("%s => set mode=sleep", self._alias)
    #         await self._driver.sleep()

    async def async_set_speed(self, speed) -> None:
        """Turn the purifier on, and set the speed."""

        if self._state.get(ATTR_AIRFLOW) != speed:
            self._state[ATTR_AIRFLOW] = speed

            await self.async_ensure_on()
            await self.async_manual()

            self._logger.debug("%s => set speed=%s", self._alias, speed)
            await getattr(self._driver, speed)()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Turn the purifier on and put it in the new preset mode."""

        preset_mode = preset_mode.strip()

        if preset_mode not in PRESET_MODES:
            values = [item.value for item in NumericPresetModes]

            # Convert the numeric preset mode to its corresponding key
            if preset_mode in values:
                index = int(preset_mode) - 1
                preset_mode = PRESET_MODES[index]
            else:
                raise ValueError(f"Invalid preset mode: {preset_mode}")

        await self.async_ensure_on()
        #self._logger.debug("%s => set mode=%s", self._alias, preset_mode)
        self._logger.debug("%s => set mode=%s", self._alias)

        # if preset_mode == PRESET_MODE_SLEEP:
        #     await self.async_sleep()
        # elif preset_mode == PRESET_MODE_AUTO:
        #     await self.async_auto()
        #     await self.async_plasmawave_on()
        # elif preset_mode == PRESET_MODE_AUTO_PLASMA_OFF:
        #     await self.async_auto()
        #     await self.async_plasmawave_off(True)
        # elif preset_mode == PRESET_MODE_MANUAL:
        #     await self.async_manual()
        #     await self.async_plasmawave_on()
        # elif preset_mode == PRESET_MODE_MANUAL_PLASMA_OFF:
        #     await self.async_manual()
        #     await self.async_plasmawave_off(True)
