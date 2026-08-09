"""The Bpost Tracker integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BpostApiClient
from .const import CONF_POSTAL_CODE, CONF_TRACKING_NUMBER, DOMAIN
from .coordinator import BpostShipmentCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA]


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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
