"""DataUpdateCoordinator for PC Link."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    API_HEALTH,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    REQUEST_TIMEOUT,
    TURN_OFF_ACTION_ENDPOINTS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class PCLinkData:
    """Data returned by the coordinator."""

    is_on: bool


class PCLinkCoordinator(DataUpdateCoordinator[PCLinkData]):
    """Coordinator to poll the pc-link health endpoint."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._host: str = entry.data[CONF_HOST]
        self._port: int = entry.data[CONF_PORT]
        self._token: str = entry.data[CONF_TOKEN]
        self._session = async_get_clientsession(hass)

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )

    @property
    def base_url(self) -> str:
        """Return the base URL for the pc-link API."""
        return f"http://{self._host}:{self._port}"

    def _headers(self) -> dict[str, str]:
        """Return auth headers."""
        return {"Authorization": f"Bearer {self._token}"}

    async def _async_update_data(self) -> PCLinkData:
        """Poll the health endpoint."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                resp = await self._session.get(
                    f"{self.base_url}{API_HEALTH}",
                    headers=self._headers(),
                )
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            return PCLinkData(is_on=False)

        if resp.status != 200:
            return PCLinkData(is_on=False)

        try:
            data = await resp.json()
        except (aiohttp.ContentTypeError, ValueError):
            return PCLinkData(is_on=False)

        return PCLinkData(is_on=data.get("status") == "ok")

    async def async_send_turn_off(self, action: str) -> None:
        """Send a turn-off command (sleep/hibernate/shutdown)."""
        endpoint = TURN_OFF_ACTION_ENDPOINTS[action]
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                await self._session.post(
                    f"{self.base_url}{endpoint}",
                    headers=self._headers(),
                )
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            _LOGGER.warning("Failed to send %s command to %s", action, self._host)
