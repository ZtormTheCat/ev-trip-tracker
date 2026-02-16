import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_ODOMETER_SENSOR,
    CONF_BATTERY_SENSOR,
    CONF_LOCATION_TRACKER,
    CONF_DRIVING_STATE_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_TRIP_END_DELAY,
    DEFAULT_TRIP_END_DELAY,
    ATTR_START_TIME,
    ATTR_END_TIME,
    ATTR_START_ODOMETER,
    ATTR_END_ODOMETER,
    ATTR_START_BATTERY,
    ATTR_END_BATTERY,
    ATTR_START_LOCATION,
    ATTR_END_LOCATION,
    ATTR_DISTANCE,
    ATTR_ENERGY_USED,
    ATTR_AVG_SPEED,
    ATTR_DURATION,
    ATTR_START_ELEVATION,
    ATTR_END_ELEVATION,
    ATTR_ELEVATION_DIFF,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EV Trip Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "trip_active": False,
        "current_trip": {},
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug("EV Trip Tracker setup complete for entry %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
