"""The Bpost Tracker integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .api import BpostApiClient
from .const import (
    CONF_POSTAL_CODE,
    CONF_REMOVE_AFTER_DAYS,
    CONF_TRACKING_NUMBER,
    DEFAULT_REMOVE_AFTER_DAYS,
    DOMAIN,
    LOGGER,
)
from .coordinator import BpostShipmentCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA]

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

SERVICE_ADD_SHIPMENT = "add_shipment"
SERVICE_ADD_SHIPMENT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TRACKING_NUMBER): cv.string,
        vol.Required(CONF_POSTAL_CODE): cv.string,
        vol.Optional("name"): cv.string,
        vol.Optional(CONF_REMOVE_AFTER_DAYS): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the bpost_tracker services."""

    async def async_handle_add_shipment(call: ServiceCall) -> None:
        """Add a shipment by driving the integration's own config flow."""
        data = {
            CONF_TRACKING_NUMBER: call.data[CONF_TRACKING_NUMBER],
            CONF_POSTAL_CODE: call.data[CONF_POSTAL_CODE],
            "name": call.data.get("name"),
        }
        if CONF_REMOVE_AFTER_DAYS in call.data:
            data[CONF_REMOVE_AFTER_DAYS] = call.data[CONF_REMOVE_AFTER_DAYS]

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=data
        )

        if result["type"] == FlowResultType.CREATE_ENTRY:
            return

        if result["type"] == FlowResultType.ABORT:
            raise HomeAssistantError(
                f"Could not add bpost shipment: {result.get('reason', 'unknown')}"
            )

        # FlowResultType.FORM: validation failed but the flow is still open
        # waiting for the next step. We won't call it again, so close it out.
        errors = result.get("errors") or {}
        hass.config_entries.flow.async_abort(result["flow_id"])
        raise HomeAssistantError(f"Could not add bpost shipment: {errors.get('base', 'unknown')}")

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_SHIPMENT, async_handle_add_shipment, schema=SERVICE_ADD_SHIPMENT_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a bpost shipment from a config entry."""
    session = async_get_clientsession(hass)
    client = BpostApiClient(session)

    coordinator = BpostShipmentCoordinator(
        hass,
        client,
        entry.data[CONF_TRACKING_NUMBER],
        entry.data[CONF_POSTAL_CODE],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    def check_auto_remove() -> None:
        """Remove this entry once it's been delivered longer than configured."""
        data = coordinator.data
        if data is None or not data.is_delivered:
            return

        remove_after_days = entry.options.get(CONF_REMOVE_AFTER_DAYS, DEFAULT_REMOVE_AFTER_DAYS)
        if not remove_after_days:
            return

        delivered_date = data.delivered_date
        if delivered_date is None:
            return

        if (dt_util.now().date() - delivered_date).days >= remove_after_days:
            LOGGER.info(
                "Removing bpost shipment %s: delivered %s days ago (limit %s)",
                entry.title,
                (dt_util.now().date() - delivered_date).days,
                remove_after_days,
            )
            hass.async_create_task(hass.config_entries.async_remove(entry.entry_id))

    # Deliberately not checked immediately: a freshly added shipment that
    # already happens to be past the removal threshold should still show up
    # at least once, not vanish before the user ever sees it. The listener
    # below covers it from the next coordinator refresh onwards.
    entry.async_on_unload(coordinator.async_add_listener(check_auto_remove))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
