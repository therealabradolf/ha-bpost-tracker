"""DataUpdateCoordinator for a single tracked bpost shipment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BpostApiClient, BpostItemNotFoundError
from .const import DOMAIN, LOGGER, UPDATE_INTERVAL_ACTIVE, UPDATE_INTERVAL_DELIVERED


def _is_delivered(item: dict[str, Any]) -> bool:
    """Whether bpost recorded an actual delivery.

    bpost uses many different activeStep.name values depending on the
    delivery method (e.g. "delivered_kariboo_point" for pickup points, vs
    plain "delivered" for a mailbox drop), so that field alone is not a
    reliable "is delivered" check. The presence of an actual delivery time
    is.
    """
    return bool((item.get("actualDeliveryInformation") or {}).get("actualDeliveryTime"))


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
        return _is_delivered(self.item)


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

        delivered = _is_delivered(item)

        stops_left = None
        if not delivered and "expectedDeliveryTimeRange" in item:
            stops_left = await self.client.async_get_stops_until_target(
                self.tracking_number, self.postal_code
            )

        self.update_interval = UPDATE_INTERVAL_DELIVERED if delivered else UPDATE_INTERVAL_ACTIVE

        return BpostShipmentData(item=item, stops_left=stops_left)
