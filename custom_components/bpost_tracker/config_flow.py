"""Config flow for the Bpost Tracker integration."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BpostApiClient, BpostItemNotFoundError
from .const import (
    CONF_POSTAL_CODE,
    CONF_REMOVE_AFTER_DAYS,
    CONF_TRACKING_NUMBER,
    DEFAULT_REMOVE_AFTER_DAYS,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TRACKING_NUMBER): str,
        vol.Required(CONF_POSTAL_CODE): str,
        vol.Optional("name"): str,
        vol.Optional(
            CONF_REMOVE_AFTER_DAYS, default=DEFAULT_REMOVE_AFTER_DAYS
        ): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)


class BpostTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle adding a single tracked bpost shipment."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial (and only) step: enter a tracking number + postal code."""
        errors: dict[str, str] = {}

        if user_input is not None:
            tracking_number = user_input[CONF_TRACKING_NUMBER].strip()
            postal_code = user_input[CONF_POSTAL_CODE].strip()

            await self.async_set_unique_id(f"{tracking_number}_{postal_code}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = BpostApiClient(session)

            try:
                await client.async_get_item(tracking_number, postal_code)
            except BpostItemNotFoundError:
                errors["base"] = "not_found"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            else:
                title = user_input.get("name") or tracking_number
                remove_after_days = user_input.get(
                    CONF_REMOVE_AFTER_DAYS, DEFAULT_REMOVE_AFTER_DAYS
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_TRACKING_NUMBER: tracking_number,
                        CONF_POSTAL_CODE: postal_code,
                    },
                    options={CONF_REMOVE_AFTER_DAYS: remove_after_days},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> BpostTrackerOptionsFlow:
        """Get the options flow for this handler."""
        return BpostTrackerOptionsFlow()


class BpostTrackerOptionsFlow(OptionsFlow):
    """Let the auto-removal delay be changed after a shipment was added."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_REMOVE_AFTER_DAYS,
                    default=self.config_entry.options.get(
                        CONF_REMOVE_AFTER_DAYS, DEFAULT_REMOVE_AFTER_DAYS
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
