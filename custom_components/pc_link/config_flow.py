"""Config flow for PC Link integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_HEALTH,
    CONF_MAC_ADDRESS,
    CONF_SCAN_INTERVAL,
    CONF_TURN_OFF_ACTION,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    REQUEST_TIMEOUT,
    TURN_OFF_ACTIONS,
    TURN_OFF_SLEEP,
)

_LOGGER = logging.getLogger(__name__)


class PCLinkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PC Link."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Deduplicate by MAC address
            await self.async_set_unique_id(
                user_input[CONF_MAC_ADDRESS].lower().replace(":", "").replace("-", "")
            )
            self._abort_if_unique_id_configured()

            # Validate connectivity
            error = await self._test_connection(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_TOKEN],
            )
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=f"PC Link ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_TOKEN): str,
                    vol.Required(CONF_MAC_ADDRESS): str,
                    vol.Required(
                        CONF_TURN_OFF_ACTION, default=TURN_OFF_SLEEP
                    ): vol.In(TURN_OFF_ACTIONS),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
                }
            ),
            errors=errors,
        )

    async def _test_connection(
        self, host: str, port: int, token: str
    ) -> str | None:
        """Test connectivity to pc-link. Returns an error key or None on success."""
        session = async_get_clientsession(self.hass)
        url = f"http://{host}:{port}{API_HEALTH}"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                resp = await session.get(url, headers=headers)
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            return "cannot_connect"

        if resp.status == 401:
            return "invalid_auth"
        if resp.status != 200:
            return "cannot_connect"

        try:
            data = await resp.json()
        except (aiohttp.ContentTypeError, ValueError):
            return "cannot_connect"

        if data.get("status") != "ok":
            return "cannot_connect"

        return None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PCLinkOptionsFlow:
        """Return the options flow handler."""
        return PCLinkOptionsFlow()


class PCLinkOptionsFlow(OptionsFlow):
    """Handle options for PC Link."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_action = self.config_entry.options.get(
            CONF_TURN_OFF_ACTION,
            self.config_entry.data.get(CONF_TURN_OFF_ACTION, TURN_OFF_SLEEP),
        )
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TURN_OFF_ACTION, default=current_action
                    ): vol.In(TURN_OFF_ACTIONS),
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current_interval
                    ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
                }
            ),
        )
