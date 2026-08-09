"""Camera platform for the Bpost Tracker integration.

Exposes the safe-place delivery picture bpost couriers leave when a parcel
is dropped off without a signature. The entity is unavailable until such a
picture exists for the shipment.
"""
from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BpostShipmentCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the bpost safe-place picture camera."""
    coordinator: BpostShipmentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BpostSafeplaceCamera(coordinator, entry)])


class BpostSafeplaceCamera(CoordinatorEntity[BpostShipmentCoordinator], Camera):
    """Picture of where the courier left the parcel, when available."""

    _attr_has_entity_name = True
    _attr_translation_key = "safeplace_picture"

    def __init__(self, coordinator: BpostShipmentCoordinator, entry: ConfigEntry) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_safeplace_picture"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _ref_id(self) -> str | None:
        item = self.coordinator.data.item
        return ((item.get("actualDeliveryInformation") or {}).get("safeplacePicture") or {}).get(
            "refId"
        )

    @property
    def available(self) -> bool:
        return super().available and self._ref_id() is not None

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        ref_id = self._ref_id()
        if ref_id is None:
            return None
        return await self.coordinator.client.async_get_safeplace_picture(ref_id)
