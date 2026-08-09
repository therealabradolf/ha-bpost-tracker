"""DataUpdateCoordinator for a single tracked bpost shipment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BpostApiClient, BpostItemNotFoundError
from .const import (
    DOMAIN,
    LOGGER,
    STATUS_DELIVERED,
    UPDATE_INTERVAL_ACTIVE,
    UPDATE_INTERVAL_DELIVERED,
)


@dataclass
class BpostShipmentData:
    """Snapshot of a shipment's tracking state."""

    item: dict[str, Any]
    stops_left: int | None

    @property
    def active_step(self) -> str | None:
        return (self.item.get("activeStep") or {}).get("name")

    @property
    def is_delivered(self) -> bool:
        return self.active_step == STATUS_DELIVERED


class BpostShipmentCoordinator(DataUpdateCoordinator[BpostShipmentData]):
    """Polls bpost for a single tracking number / postal code combination."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BpostApiClient,
        tracking_number: str,
        postal_code: str,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{tracking_number}",
            update_interval=UPDATE_INTERVAL_ACTIVE,
        )
        self.client = client
        self.tracking_number = tracking_number
        self.postal_code = postal_code

    async def _async_update_data(self) -> BpostShipmentData:
        try:
            item = await self.client.async_get_item(self.tracking_number, self.postal_code)
        except BpostItemNotFoundError as err:
            raise UpdateFailed(f"bpost has no data for this shipment: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with bpost: {err}") from err

        stops_left = None
        active_step = (item.get("activeStep") or {}).get("name")
        if active_step != STATUS_DELIVERED and "expectedDeliveryTimeRange" in item:
            stops_left = await self.client.async_get_stops_until_target(
                self.tracking_number, self.postal_code
            )

        self.update_interval = (
            UPDATE_INTERVAL_DELIVERED if active_step == STATUS_DELIVERED else UPDATE_INTERVAL_ACTIVE
        )

        return BpostShipmentData(item=item, stops_left=stops_left)
