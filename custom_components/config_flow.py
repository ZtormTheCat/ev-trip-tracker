import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_ODOMETER_SENSOR,
    CONF_BATTERY_SENSOR,
    CONF_LOCATION_TRACKER,
    CONF_DRIVING_STATE_SENSOR,
    CONF_BATTERY_CAPACITY,
)

_LOGGER = logging.getLogger(__name__)


class EVTripTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EV Trip Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="EV Trip Tracker",
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Required(CONF_DRIVING_STATE_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["binary_sensor", "sensor"])
            ),
            vol.Required(CONF_ODOMETER_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_BATTERY_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_LOCATION_TRACKER): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="device_tracker")
            ),
            vol.Required(CONF_BATTERY_CAPACITY, default=60): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=200, unit_of_measurement="kWh")
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
