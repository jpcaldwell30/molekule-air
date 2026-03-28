"""The Molekule Air integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MolekuleApiClient,
    MolekuleApiError,
    MolekuleAuthenticationError,
)
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORTED_PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.FAN)
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Molekule Air from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    client = MolekuleApiClient(
        hass,
        username,
        password,
        async_get_clientsession(hass),
    )
    if not await client.async_verify_auth():
        raise ConfigEntryAuthFailed("Invalid Molekule credentials")

    coordinator = MolekuleDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry,
        SUPPORTED_PLATFORMS,
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


class MolekuleDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Molekule device data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MolekuleApiClient,
    ) -> None:
        self.api = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest Molekule device data."""
        try:
            return await self.api.async_get_data()
        except MolekuleAuthenticationError as err:
            raise ConfigEntryAuthFailed(
                "Molekule credentials are no longer valid"
            ) from err
        except MolekuleApiError as err:
            raise UpdateFailed(str(err)) from err


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
