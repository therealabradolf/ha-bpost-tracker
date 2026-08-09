"""Config flow for the Bpost Tracker integration."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BpostApiClient, BpostItemNotFoundError
from .const import CONF_POSTAL_CODE, CONF_TRACKING_NUMBER, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TRACKING_NUMBER): str,
        vol.Required(CONF_POSTAL_CODE): str,
        vol.Optional("name"): str,
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
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_TRACKING_NUMBER: tracking_number,
                        CONF_POSTAL_CODE: postal_code,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
