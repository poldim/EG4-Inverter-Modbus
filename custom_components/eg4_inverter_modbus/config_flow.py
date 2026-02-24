"""Config flow for EG4 Modbus."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    CONF_ENABLE_READ_SENSORS,
    CONF_ENABLE_WRITE_SENSORS,
)

# Configuration schema for the initial setup.
USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST, default="localhost"): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required("slave", default=1): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        vol.Optional(
            CONF_ENABLE_READ_SENSORS,
            default=False,
        ): bool,
        vol.Optional(
            CONF_ENABLE_WRITE_SENSORS,
            default=False,
        ): bool,
    }
)

# Note: The OPTIONS_DATA_SCHEMA global variable was removed as it was unused.
# The options flow dynamically builds its schema, which is the correct approach.


class EG4ModbusConfigFlow(ConfigFlow, domain=DOMAIN):
    """EG4 Modbus config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow for this handler."""
        return EG4ModbusOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # We use the name to create a unique ID
            unique_id = f"{DOMAIN}_{user_input[CONF_NAME]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # --- START OF THE FIX ---
            # The integration reads from options, but this flow only saves to data.
            # We must populate options immediately on creation.

            # Make a copy of the user input to create the options
            options_data = user_input.copy()

            # Remove the "static" data (CONF_NAME) from the options dictionary.
            # The name is used as the title and unique ID, it shouldn't be in options.
            # All other settings (host, port, etc.) will remain in options_data.
            static_data = {
                CONF_NAME: options_data.pop(CONF_NAME)
            }

            # Create the entry, populating BOTH data (for static name)
            # and options (for all changeable settings)
            return self.async_create_entry(
                title=static_data[CONF_NAME],
                data=static_data,
                options=options_data
            )
            # --- END OF THE FIX ---

        return self.async_show_form(
            step_id="user", data_schema=USER_DATA_SCHEMA, errors=errors
        )


class EG4ModbusOptionsFlowHandler(OptionsFlow):
    """Handle EG4 Modbus options.
    
    Note: self.config_entry is automatically available from the OptionsFlow base class.
    Do not manually assign it in __init__.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # When submitted, update the options
            return self.async_create_entry(title="", data=user_input)

        # Get current data from config_entry.data (initial setup)
        # After our fix, config_data will ONLY contain CONF_NAME
        # self.config_entry is automatically available in OptionsFlow
        config_data = self.config_entry.data
        # Get current options from config_entry.options (previous options flow OR initial setup)
        # This will contain host, port, slave, etc.
        options_data = self.config_entry.options

        # Build the options schema, prioritizing options, then data, then a fallback default.
        # This logic is still correct and robust.
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=options_data.get(CONF_HOST, config_data.get(CONF_HOST, "localhost")),
                ): str,
                vol.Required(
                    CONF_PORT,
                    default=options_data.get(CONF_PORT, config_data.get(CONF_PORT, DEFAULT_PORT)),
                ): int,
                vol.Required(
                    "slave",
                    default=options_data.get("slave", config_data.get("slave", 1)),
                ): int,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options_data.get(
                        CONF_SCAN_INTERVAL,
                        config_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ),
                ): int,
                vol.Optional(
                    CONF_ENABLE_READ_SENSORS,
                    default=options_data.get(
                        CONF_ENABLE_READ_SENSORS,
                        config_data.get(CONF_ENABLE_READ_SENSORS, False),
                    ),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_WRITE_SENSORS,
                    default=options_data.get(
                        CONF_ENABLE_WRITE_SENSORS,
                        config_data.get(CONF_ENABLE_WRITE_SENSORS, False),
                    ),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)

