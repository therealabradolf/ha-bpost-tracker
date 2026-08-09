"""Thin client for the public bpost track & trace API.

This talks to the same unauthenticated JSON endpoints used by
https://track.bpost.cloud (no API key, no login). It is not an official
bpost API and bpost can change or remove it without notice.
"""
from __future__ import annotations

import base64
import binascii
from typing import Any

import aiohttp

BASE_URL = "https://track.bpost.cloud/track"


class BpostApiError(Exception):
    """Base error for the bpost API client."""


class BpostItemNotFoundError(BpostApiError):
    """Raised when bpost has no data for the given tracking number / postal code."""


class BpostApiClient:
    """Client for the bpost track & trace endpoints."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_item(self, tracking_number: str, postal_code: str) -> dict[str, Any]:
        """Fetch the current tracking item, raising BpostItemNotFoundError if unknown."""
        async with self._session.get(
            f"{BASE_URL}/items",
            params={"itemIdentifier": tracking_number, "postalCode": postal_code},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        if "error" in data:
            raise BpostItemNotFoundError(data["error"])

        items = data.get("items") or []
        if not items:
            raise BpostItemNotFoundError("NO_DATA_FOUND")

        return items[0]

    async def async_get_stops_until_target(
        self, tracking_number: str, postal_code: str
    ) -> int | None:
        """Fetch the number of stops left on the delivery round, if bpost exposes it."""
        async with self._session.get(
            f"{BASE_URL}/itemonroundstatus",
            params={"itemIdentifier": tracking_number, "postalCode": postal_code},
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)

        round_status = data.get("itemOnRoundStatus")
        if not round_status:
            return None

        stops = round_status.get("nrOfStopsUntilTarget")
        if not stops:
            return None

        return stops[0]

    async def async_get_safeplace_picture(self, ref_id: str) -> bytes | None:
        """Fetch the base64-encoded safe-place delivery picture as raw bytes."""
        async with self._session.get(f"{BASE_URL}/asset", params={"refId": ref_id}) as resp:
            if resp.status != 200:
                return None
            text = await resp.text()

        try:
            return base64.b64decode(text)
        except (ValueError, binascii.Error):
            return None
