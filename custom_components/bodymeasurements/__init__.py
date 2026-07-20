"""The Body Measurements integration."""

from __future__ import annotations

import logging

from awesomeversion import AwesomeVersion
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant

from .const import DOMAIN, HANDLERS, MIN_REQUIRED_HA_VERSION, PLATFORMS, STARTUP_MESSAGE
from .handler import MeasurementsHandler

_LOGGER = logging.getLogger(__name__)


def is_ha_supported() -> bool:
    """Return True if the running HA version is supported."""
    if AwesomeVersion(HA_VERSION) >= MIN_REQUIRED_HA_VERSION:
        return True
    _LOGGER.error(
        'Unsupported HA version! Please upgrade home assistant at least to "%s"',
        MIN_REQUIRED_HA_VERSION,
    )
    return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Body Measurements from a config entry."""
    if not is_ha_supported():
        return False

    if hass.data.get(DOMAIN) is None:
        hass.data[DOMAIN] = {HANDLERS: {}}
        _LOGGER.info(STARTUP_MESSAGE)

    config = {**entry.data, **entry.options}
    handler = MeasurementsHandler(hass, config, entry.entry_id)
    hass.data[DOMAIN][HANDLERS][entry.entry_id] = handler

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        handler: MeasurementsHandler = hass.data[DOMAIN][HANDLERS].pop(entry.entry_id)
        handler.unload()
        if not hass.data[DOMAIN][HANDLERS]:
            hass.data.pop(DOMAIN)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
