"""The EG4 Modbus Integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN, 
    DEFAULT_SCAN_INTERVAL, 
    CONF_ENABLE_READ_SENSORS, 
    CONF_ENABLE_WRITE_SENSORS,
    INPUT_REGISTERS,
    HOLDING_REGISTERS,
)
from .hub import EG4ModbusHub

_LOGGER = logging.getLogger(__name__)

# Define the platforms that this integration will support.
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an EG4 Modbus device from a config entry."""
    name = entry.data[CONF_NAME]
    
    # Retrieve configuration from the `options` instead of `data`
    host = entry.options.get(CONF_HOST)
    port = entry.options.get(CONF_PORT)
    slave = entry.options.get("slave")
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = EG4ModbusHub(hass, name, host, port, slave, scan_interval)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    # Set up the options listener. This will reload the integration when options change.
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Forward the setup to all defined platforms.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Update entity registry based on checkbox settings
    await _update_entity_registry(hass, entry)

    return True


async def _update_entity_registry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update entity registry to enable/disable entities based on checkbox settings."""
    registry = er.async_get(hass)
    enable_read_sensors = entry.options.get(CONF_ENABLE_READ_SENSORS, False)
    enable_write_sensors = entry.options.get(CONF_ENABLE_WRITE_SENSORS, False)
    
    # Get all entities for this entry
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    
    # Build a map of unique_id -> default enabled state from entity descriptions
    default_enabled_map = {}
    name = entry.data[CONF_NAME]
    
    # Check input registers (sensors/binary_sensors)
    for desc in INPUT_REGISTERS.values():
        unique_id = f"{name}_{desc.key}"
        default_enabled_map[unique_id] = desc.entity_registry_enabled_default
    
    # Check holding registers (sensors/numbers/selects)
    for desc in HOLDING_REGISTERS.values():
        unique_id = f"{name}_{desc.key}"
        default_enabled_map[unique_id] = desc.entity_registry_enabled_default
    
    for entity_entry in entities:
        entity_id = entity_entry.entity_id
        domain = entity_entry.domain
        unique_id = entity_entry.unique_id
        
        # Determine if this entity should be enabled
        should_enable = None
        
        if domain == "sensor" or domain == "binary_sensor":
            if enable_read_sensors:
                # Checkbox checked: enable all read sensors
                should_enable = True
            else:
                # Checkbox unchecked: use default from entity description
                should_enable = default_enabled_map.get(unique_id, True)
        elif domain == "number" or domain == "select":
            if enable_write_sensors:
                # Checkbox checked: enable all write sensors
                should_enable = True
            else:
                # Checkbox unchecked: use default from entity description
                should_enable = default_enabled_map.get(unique_id, False)
        
        # Update entity if needed
        if should_enable is not None:
            is_currently_enabled = entity_entry.disabled_by is None
            if is_currently_enabled != should_enable:
                registry.async_update_entity(
                    entity_id, 
                    disabled_by=None if should_enable else er.RegistryEntryDisabler.INTEGRATION
                )
                _LOGGER.debug("Updated entity %s (%s): enabled=%s", entity_id, unique_id, should_enable)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an EG4 modbus entry."""
    # Unload platforms in parallel.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Clean up the hub from `hass.data`.
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        hub.close()  # Ensure cleanup

    return unload_ok
