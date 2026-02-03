import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EV Trip Tracker sensors."""
    config = entry.data

    current_trip_sensor = EVCurrentTripSensor(hass, entry, config)
    last_trip_sensor = EVLastTripSensor(hass, entry)

    async_add_entities([current_trip_sensor, last_trip_sensor])


class EVCurrentTripSensor(SensorEntity):
    """Sensor for current/active trip."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, config: dict) -> None:
        self.hass = hass
        self._entry = entry
        self._config = config
        self._attr_name = "EV Current Trip"
        self._attr_unique_id = f"{entry.entry_id}_current_trip"
        self._state = "idle"
        self._trip_data = {}
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        """Start tracking state changes."""
        self._unsub = async_track_state_change_event(
            self.hass,
            [self._config[CONF_DRIVING_STATE_SENSOR]],
            self._handle_driving_state_change,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up."""
        if self._unsub:
            self._unsub()

    @callback
    def _handle_driving_state_change(self, event) -> None:
        """Handle driving state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        is_driving = new_state.state in ["on", "driving", "true", "True", True]

        if is_driving and self._state == "idle":
            self.hass.async_create_task(self._start_trip())
        elif not is_driving and self._state == "active":
            self.hass.async_create_task(self._end_trip())

    async def _start_trip(self) -> None:
        """Start a new trip."""
        _LOGGER.info("Trip started")
        self._state = "active"

        odometer = self.hass.states.get(self._config[CONF_ODOMETER_SENSOR])
        battery = self.hass.states.get(self._config[CONF_BATTERY_SENSOR])
        location = self.hass.states.get(self._config[CONF_LOCATION_TRACKER])

        lat = location.attributes.get("latitude") if location else None
        lon = location.attributes.get("longitude") if location else None

        self._trip_data = {
            ATTR_START_TIME: datetime.now().isoformat(),
            ATTR_START_ODOMETER: float(odometer.state) if odometer else None,
            ATTR_START_BATTERY: float(battery.state) if battery else None,
            "start_latitude": lat,
            "start_longitude": lon,
            ATTR_START_ELEVATION: await self._get_elevation(lat, lon)
            if lat and lon
            else None,
        }
        self.async_write_ha_state()

    async def _end_trip(self) -> None:
        """End the current trip."""
        _LOGGER.info("Trip ended")

        odometer = self.hass.states.get(self._config[CONF_ODOMETER_SENSOR])
        battery = self.hass.states.get(self._config[CONF_BATTERY_SENSOR])
        location = self.hass.states.get(self._config[CONF_LOCATION_TRACKER])

        lat = location.attributes.get("latitude") if location else None
        lon = location.attributes.get("longitude") if location else None

        self._trip_data[ATTR_END_TIME] = datetime.now().isoformat()
        self._trip_data[ATTR_END_ODOMETER] = float(odometer.state) if odometer else None
        self._trip_data[ATTR_END_BATTERY] = float(battery.state) if battery else None
        self._trip_data["end_latitude"] = lat
        self._trip_data["end_longitude"] = lon
        self._trip_data[ATTR_END_ELEVATION] = (
            await self._get_elevation(lat, lon) if lat and lon else None
        )

        self._calculate_trip_metrics()

        self.hass.data[DOMAIN][self._entry.entry_id]["last_trip"] = (
            self._trip_data.copy()
        )
        self.hass.bus.async_fire(f"{DOMAIN}_trip_completed", self._trip_data)

        self._state = "idle"
        self._trip_data = {}
        self.async_write_ha_state()

    def _calculate_trip_metrics(self) -> None:
        """Calculate distance, energy, avg speed."""
        start_odo = self._trip_data.get(ATTR_START_ODOMETER)
        end_odo = self._trip_data.get(ATTR_END_ODOMETER)
        start_bat = self._trip_data.get(ATTR_START_BATTERY)
        end_bat = self._trip_data.get(ATTR_END_BATTERY)
        start_time = datetime.fromisoformat(self._trip_data[ATTR_START_TIME])
        end_time = datetime.fromisoformat(self._trip_data[ATTR_END_TIME])

        # Distance
        if start_odo and end_odo:
            self._trip_data[ATTR_DISTANCE] = round(end_odo - start_odo, 2)

        # Energy used (kWh)
        if start_bat and end_bat:
            battery_capacity = self._config[CONF_BATTERY_CAPACITY]
            energy = (start_bat - end_bat) / 100 * battery_capacity
            self._trip_data[ATTR_ENERGY_USED] = round(energy, 2)

        # Duration
        duration = end_time - start_time
        self._trip_data[ATTR_DURATION] = str(duration)

        # Average speed
        if self._trip_data.get(ATTR_DISTANCE) and duration.total_seconds() > 0:
            hours = duration.total_seconds() / 3600
            self._trip_data[ATTR_AVG_SPEED] = round(
                self._trip_data[ATTR_DISTANCE] / hours, 1
            )

        # Elevation diff
        start_elev = self._trip_data.get(ATTR_START_ELEVATION)
        end_elev = self._trip_data.get(ATTR_END_ELEVATION)
        if start_elev is not None and end_elev is not None:
            self._trip_data[ATTR_ELEVATION_DIFF] = round(end_elev - start_elev, 1)

    async def _get_elevation(self, lat: float, lon: float) -> float | None:
        """Fetch elevation from Open-Elevation API."""
        try:
            session = async_get_clientsession(self.hass)
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            async with session.get(url) as response:
                data = await response.json()
                return data["results"][0]["elevation"]
        except Exception as e:
            _LOGGER.warning("Failed to fetch elevation: %s", e)
            return None

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._trip_data


class EVLastTripSensor(SensorEntity):
    """Sensor for last completed trip."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "EV Last Trip"
        self._attr_unique_id = f"{entry.entry_id}_last_trip"
        self._attr_native_unit_of_measurement = "km"

    @property
    def state(self):
        last_trip = self.hass.data[DOMAIN][self._entry.entry_id].get("last_trip", {})
        return last_trip.get(ATTR_DISTANCE)

    @property
    def extra_state_attributes(self):
        return self.hass.data[DOMAIN][self._entry.entry_id].get("last_trip", {})
