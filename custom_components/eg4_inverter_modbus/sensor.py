from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    INPUT_REGISTERS,
    HOLDING_REGISTERS,
    EG4ModbusSensorEntityDescription,
    ATTR_MANUFACTURER,
    CONF_ENABLE_ALL_READ_SENSORS,
)
from .hub import EG4ModbusHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EG4 sensors."""
    hub: EG4ModbusHub = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    enable_read_sensors = entry.options.get(CONF_ENABLE_ALL_READ_SENSORS, entry.options.get("enable_read_sensors", False))

    # Create sensors from Input Registers
    for key, description in INPUT_REGISTERS.items():
        if isinstance(description, EG4ModbusSensorEntityDescription):
            # For iteration, we might iterate values or items. OLD code iterated values.
            # But keys in INPUT_REGISTERS are ints.
            # No changes needed for Input Registers loop if we iterate values, 
            # as they don't seem to use bitmask addressing in this list?
            # Actually, let's keep it safe.
            is_enabled = description.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            dev_info = hub.get_device_info(description.key, description.entity_category)
            entities.append(EG4Sensor(hub, dev_info, description, is_enabled))

    # Create sensors from Holding Registers
    for key, description in HOLDING_REGISTERS.items():
        if isinstance(description, EG4ModbusSensorEntityDescription):
            address = description.address if description.address is not None else key
            # Skip if address is somehow not an int (shouldn't happen with our logic, unless key is str and no address)
            # If key is string (new registers), address MUST be set.
            if not isinstance(address, int):
                 # Fallback: if key is int, use it.
                 if isinstance(key, int):
                     address = key
                 else:
                     continue

            is_enabled = description.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            dev_info = hub.get_device_info(description.key, description.entity_category)
            entities.append(EG4Sensor(hub, dev_info, description, is_enabled))

    from dataclasses import replace
    from .const import BATTERY_SENSOR_DEFINITIONS

    # Create dynamic battery sensors
    for i in range(hub.battery_count):
        battery_num = i + 1
        prefix = f"battery{battery_num:02d}"
        
        for base_key, base_desc in BATTERY_SENSOR_DEFINITIONS.items():
            new_key = base_desc.key.format(prefix)
            new_name = base_desc.name.format(battery_num)
            desc = replace(base_desc, key=new_key, name=new_name)
            
            is_enabled = desc.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            dev_info = hub.get_device_info(desc.key, desc.entity_category)
            entities.append(EG4Sensor(hub, dev_info, desc, is_enabled))

    async_add_entities(entities)


class EG4Sensor(CoordinatorEntity[EG4ModbusHub], SensorEntity):
    """Representation of an EG4 Modbus sensor."""

    entity_description: EG4ModbusSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        hub: EG4ModbusHub,
        device_info: dict,
        description: EG4ModbusSensorEntityDescription,
        enabled_default: bool,  # <-- Add this argument
    ):
        """Initialize the sensor."""
        super().__init__(coordinator=hub)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{hub.name}_{description.key}"
        self._attr_name = description.name
        self._attr_suggested_display_precision = description.suggested_display_precision
        self._attr_entity_enabled_default = enabled_default  # <-- Use the argument

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self.entity_description.key.endswith("_cell_temp_delta"):
            return self.coordinator.hass.config.units.temperature_unit
        return self.entity_description.native_unit_of_measurement
