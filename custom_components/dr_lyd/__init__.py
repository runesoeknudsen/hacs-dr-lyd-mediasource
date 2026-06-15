"""The DR LYD integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DRLydClient
from .const import CONF_API_KEY, DEFAULT_API_KEY

type DRLydConfigEntry = ConfigEntry[DRLydClient]

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: DRLydConfigEntry) -> bool:
    """Set up DR LYD from a config entry."""
    session = async_get_clientsession(hass)
    api_key = entry.data.get(CONF_API_KEY, DEFAULT_API_KEY)
    entry.runtime_data = DRLydClient(session, api_key)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DRLydConfigEntry) -> bool:
    """Unload a DR LYD config entry."""
    return True
