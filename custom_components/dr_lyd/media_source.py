"""Expose the DR LYD catalog as a Home Assistant media source."""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from typing import Any

from homeassistant.components.media_player import BrowseError, MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .api import DRLydClient, DRLydError, parse_publish_time, pick_audio_url
from .const import CATALOG_TTL, DOMAIN, IMAGE_BASE

_LOGGER = logging.getLogger(__name__)

MIME_TYPE = "audio/mpeg"


async def async_get_media_source(hass: HomeAssistant) -> DRLydMediaSource:
    """Set up the DR LYD media source."""
    return DRLydMediaSource(hass)


def _image_url(image_assets: list[dict] | None) -> str | None:
    """Build a thumbnail URL from a DR image asset list (prefer square)."""
    if not image_assets:
        return None
    square = next(
        (a for a in image_assets if a.get("ratio") == "1:1" and a.get("id")),
        None,
    )
    chosen = square or next((a for a in image_assets if a.get("id")), None)
    if not chosen:
        return None
    return f"{IMAGE_BASE}/{chosen['id']}"


def _encode(value: str) -> str:
    """URL-safe base64 encode a string for use in an identifier."""
    return base64.urlsafe_b64encode(value.encode()).decode()


def _decode(value: str) -> str:
    """Decode an identifier segment produced by _encode."""
    return base64.urlsafe_b64decode(value.encode()).decode()


def _format_duration(milliseconds: Any) -> str:
    """Format a millisecond duration as H:MM or M:SS."""
    try:
        total_seconds = int(milliseconds) // 1000
    except (TypeError, ValueError):
        return ""
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


class DRLydMediaSource(MediaSource):
    """Provide DR LYD podcasts as a browsable media source."""

    name = "DR LYD"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the media source."""
        super().__init__(DOMAIN)
        self.hass = hass
        self._catalog: list[dict] = []
        self._catalog_time: datetime | None = None

    def _get_client(self) -> DRLydClient:
        """Return the API client from a loaded config entry."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            client = getattr(entry, "runtime_data", None)
            if client is not None:
                return client
        raise BrowseError("DR LYD integration is not set up")

    async def _async_catalog(self) -> list[dict]:
        """Return the cached series catalog, refreshing it when stale."""
        now = dt_util.utcnow()
        if (
            self._catalog
            and self._catalog_time is not None
            and now - self._catalog_time < CATALOG_TTL
        ):
            return self._catalog
        client = self._get_client()
        try:
            self._catalog = await client.async_list_series()
        except DRLydError as err:
            if self._catalog:
                _LOGGER.warning("Using stale DR LYD catalog: %s", err)
                return self._catalog
            raise BrowseError(f"Unable to load DR LYD catalog: {err}") from err
        self._catalog_time = now
        return self._catalog

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a playable episode identifier into a stream URL."""
        identifier = item.identifier or ""
        prefix, _, rest = identifier.partition("/")
        if prefix != "e" or not rest:
            raise Unresolvable(f"Cannot resolve DR LYD item: {identifier}")
        try:
            url = _decode(rest)
        except (ValueError, UnicodeDecodeError) as err:
            raise Unresolvable(f"Invalid DR LYD item: {identifier}") from err
        return PlayMedia(url, MIME_TYPE)

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Browse the DR LYD catalog."""
        identifier = item.identifier or ""
        prefix, _, rest = identifier.partition("/")

        if not identifier:
            return self._build_root()
        if identifier == "cat":
            return await self._build_category_list()
        if prefix == "cat":
            return await self._build_series_in_category(rest)
        if identifier == "az":
            return await self._build_letter_list()
        if prefix == "az":
            return await self._build_series_for_letter(rest)
        if prefix == "s":
            return await self._build_episode_list(rest)

        raise BrowseError(f"Unknown DR LYD path: {identifier}")

    def _build_root(self) -> BrowseMediaSource:
        """Build the top-level browse entries."""
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier="cat",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.PODCAST,
                title="Kategorier",
                can_play=False,
                can_expand=True,
            ),
            BrowseMediaSource(
                domain=DOMAIN,
                identifier="az",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.PODCAST,
                title="Alle programmer (A-Å)",
                can_play=False,
                can_expand=True,
            ),
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.PODCAST,
            title="DR LYD",
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.DIRECTORY,
        )

    async def _build_category_list(self) -> BrowseMediaSource:
        """List all categories present in the catalog."""
        catalog = await self._async_catalog()
        categories: set[str] = set()
        for series in catalog:
            for category in series.get("categories") or []:
                if category:
                    categories.add(category)
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"cat/{name}",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.PODCAST,
                title=name,
                can_play=False,
                can_expand=True,
            )
            for name in sorted(categories, key=str.casefold)
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="cat",
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.PODCAST,
            title="Kategorier",
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.DIRECTORY,
        )

    async def _build_series_in_category(self, category: str) -> BrowseMediaSource:
        """List series belonging to a category."""
        catalog = await self._async_catalog()
        series = [
            s for s in catalog if category in (s.get("categories") or [])
        ]
        return self._series_directory(
            identifier=f"cat/{category}",
            title=category,
            series_list=series,
        )

    async def _build_letter_list(self) -> BrowseMediaSource:
        """List the first-letter groups present in the catalog."""
        catalog = await self._async_catalog()
        letters: set[str] = set()
        for series in catalog:
            letter = (series.get("sortLetter") or "#").upper()
            letters.add(letter)
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"az/{letter}",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.PODCAST,
                title=letter,
                can_play=False,
                can_expand=True,
            )
            for letter in sorted(letters, key=str.casefold)
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="az",
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.PODCAST,
            title="Alle programmer (A-Å)",
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.DIRECTORY,
        )

    async def _build_series_for_letter(self, letter: str) -> BrowseMediaSource:
        """List series whose sort letter matches."""
        catalog = await self._async_catalog()
        target = letter.upper()
        series = [
            s
            for s in catalog
            if (s.get("sortLetter") or "#").upper() == target
        ]
        return self._series_directory(
            identifier=f"az/{letter}",
            title=letter,
            series_list=series,
        )

    def _series_directory(
        self, identifier: str, title: str, series_list: list[dict]
    ) -> BrowseMediaSource:
        """Build a directory listing the given series."""
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"s/{series['id']}",
                media_class=MediaClass.PODCAST,
                media_content_type=MediaType.PODCAST,
                title=series.get("title", "Ukendt"),
                can_play=False,
                can_expand=True,
                thumbnail=_image_url(series.get("imageAssets")),
            )
            for series in sorted(
                series_list,
                key=lambda s: str(s.get("title", "")).casefold(),
            )
            if series.get("id")
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.PODCAST,
            title=title,
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.PODCAST,
        )

    async def _build_episode_list(self, urn: str) -> BrowseMediaSource:
        """List the episodes of a series, newest first."""
        client = self._get_client()
        catalog = await self._async_catalog()
        series = next((s for s in catalog if s.get("id") == urn), None)
        if series is None:
            try:
                series = await client.async_get_series(urn)
            except DRLydError:
                series = {}
        series_title = series.get("title", "DR LYD")
        series_image = _image_url(series.get("imageAssets"))

        try:
            episodes = await client.async_list_episodes(urn)
        except DRLydError as err:
            raise BrowseError(f"Unable to load episodes: {err}") from err

        episodes.sort(
            key=lambda e: parse_publish_time(e.get("publishTime"))
            or datetime.min,
            reverse=True,
        )

        children: list[BrowseMediaSource] = []
        for episode in episodes:
            url = pick_audio_url(episode.get("audioAssets") or [])
            if not url:
                continue
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"e/{_encode(url)}",
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=self._episode_title(episode),
                    can_play=True,
                    can_expand=False,
                    thumbnail=_image_url(episode.get("imageAssets"))
                    or series_image,
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"s/{urn}",
            media_class=MediaClass.PODCAST,
            media_content_type=MediaType.PODCAST,
            title=series_title,
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.MUSIC,
            thumbnail=series_image,
        )

    @staticmethod
    def _episode_title(episode: dict) -> str:
        """Compose a readable episode title with date and duration."""
        title = episode.get("title", "Afsnit")
        published = parse_publish_time(episode.get("publishTime"))
        parts: list[str] = [title]
        meta: list[str] = []
        if published:
            meta.append(published.strftime("%d-%m-%Y"))
        duration = _format_duration(episode.get("durationMilliseconds"))
        if duration:
            meta.append(duration)
        if meta:
            parts.append(f"({' · '.join(meta)})")
        return " ".join(parts)
