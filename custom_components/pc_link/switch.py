"""Switch platform for PC Link."""

from __future__ import annotations

import logging
from typing import Any

import wakeonlan
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC_ADDRESS, CONF_TURN_OFF_ACTION, DOMAIN, TURN_OFF_SLEEP
from .coordinator import PCLinkCoordinator, PCLinkData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PC Link switch from a config entry."""
    coordinator: PCLinkCoordinator = entry.runtime_data
    async_add_entities([PCLinkSwitch(coordinator, entry)])


class PCLinkSwitch(CoordinatorEntity[PCLinkCoordinator], SwitchEntity):
    """Representation of a PC Link switch."""

    _attr_has_entity_name = True
    _attr_name = "Power"

    def __init__(
        self,
        coordinator: PCLinkCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._mac_address: str = entry.data[CONF_MAC_ADDRESS]
        self._host: str = entry.data[CONF_HOST]
        self._entry = entry

        mac_normalized = self._mac_address.lower().replace(":", "").replace("-", "")
        self._attr_unique_id = f"{mac_normalized}_power"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_normalized)},
            name=f"PC ({self._host})",
            manufacturer="PC Link",
            connections={("mac", self._mac_address)},
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the PC is on."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the PC via Wake-on-LAN."""
        _LOGGER.debug("Sending WoL magic packet to %s", self._mac_address)
        await self.hass.async_add_executor_job(
            wakeonlan.send_magic_packet, self._mac_address
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the PC using the configured action."""
        action = self._entry.options.get(
            CONF_TURN_OFF_ACTION,
            self._entry.data.get(CONF_TURN_OFF_ACTION, TURN_OFF_SLEEP),
        )
        _LOGGER.debug("Sending %s command to %s", action, self._host)
        await self.coordinator.async_send_turn_off(action)
