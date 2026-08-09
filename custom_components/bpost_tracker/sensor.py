"""Sensor platform for the Bpost Tracker integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity

from .const import CONF_POSTAL_CODE, CONF_TRACKING_NUMBER, DEFAULT_LANGUAGE, DOMAIN, SUPPORTED_LANGUAGES
from .coordinator import BpostShipmentCoordinator, BpostShipmentData


def _language(hass: HomeAssistant) -> str:
    """Map the HA-configured language to one bpost supports, defaulting to English."""
    lang = (hass.config.language or "").split("-")[0].upper()
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the bpost shipment status sensor."""
    coordinator: BpostShipmentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BpostShipmentStatusSensor(coordinator, entry)])


class BpostShipmentStatusSensor(CoordinatorEntity[BpostShipmentCoordinator], SensorEntity):
    """Represents the tracking status of a single bpost shipment."""

    _attr_has_entity_name = True
    _attr_translation_key = "status"
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator: BpostShipmentCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="bpost",
            model="Shipment",
        )

    @property
    def data(self) -> BpostShipmentData:
        return self.coordinator.data

    @property
    def native_value(self) -> str | None:
        return self.data.active_step

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self.data.item
        lang = _language(self.coordinator.hass)

        events = item.get("events") or []
        latest_event = events[0] if events else {}
        description = ((latest_event.get("key") or {}).get(lang) or {}).get("description")

        delivery_range = item.get("expectedDeliveryTimeRange") or {}
        sender = item.get("senderCommercialName") or (item.get("sender") or {}).get("name")

        attributes: dict[str, Any] = {
            "tracking_number": self._entry.data[CONF_TRACKING_NUMBER],
            "postal_code": self._entry.data[CONF_POSTAL_CODE],
            "status_description": description,
            "status_time": latest_event.get("time"),
            "sender": sender,
        }

        if delivery_range:
            attributes["expected_delivery_from"] = delivery_range.get("time1")
            attributes["expected_delivery_to"] = delivery_range.get("time2")

        if self.data.stops_left is not None:
            attributes["stops_until_delivery"] = self.data.stops_left

        return attributes
