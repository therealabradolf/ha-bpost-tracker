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

# A stalled bpost must not block a config flow or a coordinator refresh for
# aiohttp's default of five minutes.
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)

# Safe-place photos are far smaller than this; the cap only guards memory.
MAX_PICTURE_BASE64_BYTES = 5 * 1024 * 1024

_IMAGE_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")  # JPEG, PNG


class BpostApiError(Exception):
    """Base error for the bpost API client."""


class BpostItemNotFoundError(BpostApiError):
    """Raised when bpost has no data for the given tracking number / postal code."""


def _decode_picture(payload: bytes) -> bytes | None:
    """Strictly decode a base64 picture, returning None unless it is a JPEG/PNG.

    bpost answers HTTP 200 with a JSON error body (e.g. {"error":"WRONG_ASSET_KEY"})
    for unknown assets, so the body must not be trusted to be an image.
    """
    try:
        image = base64.b64decode(b"".join(payload.split()), validate=True)
    except binascii.Error:
        return None
    return image if image.startswith(_IMAGE_SIGNATURES) else None


class BpostApiClient:
    """Client for the bpost track & trace endpoints."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_item(self, tracking_number: str, postal_code: str) -> dict[str, Any]:
        """Fetch the current tracking item, raising BpostItemNotFoundError if unknown."""
        async with self._session.get(
            f"{BASE_URL}/items",
            params={"itemIdentifier": tracking_number, "postalCode": postal_code},
            timeout=REQUEST_TIMEOUT,
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
        """Fetch the number of stops left on the delivery round, if bpost exposes it.

        Best effort: any failure just means "unknown" and must not fail the
        whole shipment update.
        """
        try:
            async with self._session.get(
                f"{BASE_URL}/itemonroundstatus",
                params={"itemIdentifier": tracking_number, "postalCode": postal_code},
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError):
            return None

        round_status = data.get("itemOnRoundStatus")
        if not round_status:
            return None

        stops = round_status.get("nrOfStopsUntilTarget")
        if not stops:
            return None

        return stops[0]

    async def async_get_safeplace_picture(self, ref_id: str) -> bytes | None:
        """Fetch the safe-place delivery picture as raw JPEG/PNG bytes, or None."""
        payload = bytearray()
        try:
            async with self._session.get(
                f"{BASE_URL}/asset", params={"refId": ref_id}, timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status != 200:
                    return None
                async for chunk in resp.content.iter_chunked(65536):
                    payload += chunk
                    if len(payload) > MAX_PICTURE_BASE64_BYTES:
                        return None
        except (aiohttp.ClientError, TimeoutError):
            return None

        return _decode_picture(bytes(payload))
