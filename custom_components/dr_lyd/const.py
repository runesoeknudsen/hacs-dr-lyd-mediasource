"""Constants for the DR LYD integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "dr_lyd"

# DR LYD internal API. This is not an officially documented public API, so the
# API key may be rotated by DR at any time. The user can override it via the
# config flow by reading a fresh "x-apikey" header from dr.dk/lyd (DevTools).
API_BASE = "https://api.dr.dk/radio/v2"
IMAGE_BASE = "https://asset.dr.dk/drlyd/images"
DEFAULT_API_KEY = "6Wkh8s98Afx1ZAaTT4FuWODTmvWGDPpR"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
)

CONF_API_KEY = "api_key"

# How long the full series catalog is cached before being re-fetched.
CATALOG_TTL = timedelta(hours=6)

# Number of series fetched per request (the catalog is ~700 items).
SERIES_PAGE_LIMIT = 1000
# Number of episodes fetched per request when expanding a series.
EPISODES_PAGE_LIMIT = 256
