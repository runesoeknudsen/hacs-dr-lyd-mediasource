"""Async client for the DR LYD (dr.dk/lyd) audio API."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp

from .const import (
    API_BASE,
    EPISODES_PAGE_LIMIT,
    SERIES_PAGE_LIMIT,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20


class DRLydError(Exception):
    """Generic DR LYD API error."""


class DRLydAuthError(DRLydError):
    """Raised when the API key is rejected by DR."""


class DRLydClient:
    """Thin async wrapper around the DR LYD series/episodes endpoints."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialise the client with a shared aiohttp session and API key."""
        self._session = session
        self._api_key = api_key

    @property
    def api_key(self) -> str:
        """Return the configured API key."""
        return self._api_key

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> dict:
        """Perform a GET request against the DR LYD API."""
        headers = {
            "x-apikey": self._api_key,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "Referer": "https://www.dr.dk/",
        }
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(
                    url, params=params, headers=headers
                )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise DRLydError(f"Error communicating with DR LYD: {err}") from err

        if response.status in (401, 403):
            raise DRLydAuthError(
                f"DR LYD rejected the API key (HTTP {response.status})"
            )
        if response.status != 200:
            text = await response.text()
            raise DRLydError(
                f"Unexpected response from DR LYD (HTTP {response.status}): {text[:200]}"
            )
        return await response.json()

    async def async_validate(self) -> None:
        """Validate the API key by requesting a single series."""
        await self._get(f"{API_BASE}/series", params={"limit": 1})

    async def async_list_series(self) -> list[dict]:
        """Return the full catalog of series (podcasts/programmes)."""
        data = await self._get(
            f"{API_BASE}/series", params={"limit": SERIES_PAGE_LIMIT}
        )
        items: list[dict] = list(data.get("items", []))
        next_url = data.get("next")
        # Defensive pagination in case the catalog ever exceeds the page limit.
        while next_url:
            data = await self._get(next_url)
            items.extend(data.get("items", []))
            next_url = data.get("next")
        return items

    async def async_get_series(self, urn: str) -> dict:
        """Return details for a single series by URN."""
        return await self._get(f"{API_BASE}/series/{urn}")

    async def async_list_episodes(self, urn: str) -> list[dict]:
        """Return all episodes for a series, following pagination."""
        items: list[dict] = []
        url: str | None = f"{API_BASE}/series/{urn}/episodes"
        params: dict[str, Any] | None = {"limit": EPISODES_PAGE_LIMIT}
        while url:
            data = await self._get(url, params=params)
            items.extend(data.get("items", []))
            url = data.get("next")
            params = None  # next already carries query params
        return items


def pick_audio_url(audio_assets: list[dict]) -> str | None:
    """Pick the best progressive MP3 asset (closest to 192 kbps)."""
    candidates = [
        asset
        for asset in audio_assets
        if asset.get("target") == "Progressive"
        and asset.get("format") == "mp3"
        and asset.get("url")
    ]
    if not candidates:
        # Fall back to any progressive asset with a URL.
        candidates = [
            asset
            for asset in audio_assets
            if asset.get("target") == "Progressive" and asset.get("url")
        ]
    if not candidates:
        return None
    best = min(candidates, key=lambda a: abs(int(a.get("bitrate") or 0) - 192))
    return best["url"]


def parse_publish_time(value: str | None) -> datetime | None:
    """Parse an ISO-8601 publish time, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
