from __future__ import annotations

import logging

from typing import Union

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
    EG4ModbusNumberEntityDescription,
    EG4ModbusSelectEntityDescription,
    EG4ModbusTimeEntityDescription,
    ATTR_MANUFACTURER,
    CONF_ENABLE_ALL_READ_SENSORS,
    CONF_ENABLE_WRITE_SENSORS,
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
    enable_write_sensors = entry.options.get(CONF_ENABLE_WRITE_SENSORS, False)

    # Create sensors from Input Registers
    for key, description in INPUT_REGISTERS.items():
        if isinstance(description, EG4ModbusSensorEntityDescription):
            is_enabled = description.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            dev_info = hub.get_device_info(description.key, description.entity_category)
            entities.append(EG4Sensor(hub, dev_info, description, is_enabled))

    # Create sensors from Holding Registers
    for key, description in HOLDING_REGISTERS.items():
        if isinstance(description, EG4ModbusSensorEntityDescription):
            address = description.address if description.address is not None else key
            # Skip if address is somehow not an int
            if not isinstance(address, int):
                if isinstance(key, int):
                    address = key
                else:
                    continue

            is_enabled = description.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            dev_info = hub.get_device_info(description.key, description.entity_category)
            entities.append(EG4Sensor(hub, dev_info, description, is_enabled))
        elif isinstance(description, (EG4ModbusNumberEntityDescription, EG4ModbusSelectEntityDescription, EG4ModbusTimeEntityDescription)):
            # Mirror sensor for writable register: active as read-only when write sensors are disabled
            is_ro_enabled = not enable_write_sensors
            dev_info = hub.get_device_info(description.key, description.entity_category)
            entities.append(EG4ReadOnlyHoldingSensor(hub, dev_info, description, is_ro_enabled))

    from dataclasses import replace
    from .const import BATTERY_SENSOR_DEFINITIONS

    # Create dynamic battery sensors
    for i in range(hub.battery_count):
        battery_num = i + 1
        prefix = f"battery{battery_num:02d}"
        
        for base_key, base_desc in BATTERY_SENSOR_DEFINITIONS.items():
            new_key = base_desc.key.format(prefix)
            new_name = base_desc.name.format(battery_num) if "{}" in base_desc.name else base_desc.name
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
        self._attr_entity_registry_enabled_default = enabled_default

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


class EG4ReadOnlyHoldingSensor(CoordinatorEntity[EG4ModbusHub], SensorEntity):
    """Representation of a read-only mirror sensor for a writable holding register."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hub: EG4ModbusHub,
        device_info: dict,
        description: Union[
            EG4ModbusNumberEntityDescription,
            EG4ModbusSelectEntityDescription,
            EG4ModbusTimeEntityDescription,
        ],
        enabled_default: bool,
    ):
        """Initialize the read-only holding sensor."""
        super().__init__(coordinator=hub)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{hub.name}_{description.key}"
        self._attr_name = description.name
        self._attr_entity_registry_enabled_default = enabled_default
        self._attr_icon = description.icon
        if description.entity_category is not None:
            self._attr_entity_category = description.entity_category

        if isinstance(description, EG4ModbusNumberEntityDescription):
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement
            if description.device_class is not None:
                self._attr_device_class = description.device_class
            if description.scale != 1.0:
                self._attr_suggested_display_precision = 1
            else:
                self._attr_suggested_display_precision = 0

    @property
    def native_value(self):
        """Return the state of the read-only holding sensor."""
        desc = self.entity_description
        if isinstance(desc, EG4ModbusSelectEntityDescription):
            val = self.coordinator.data.get(desc.key)
            if val is None:
                return None
            if desc.option_dict:
                try:
                    return desc.option_dict[int(val)]
                except (ValueError, KeyError):
                    pass
            try:
                return desc.options[int(val)]
            except (ValueError, IndexError):
                s_val = str(val)
                if s_val in desc.options:
                    return s_val
                return str(val)

        elif isinstance(desc, EG4ModbusTimeEntityDescription):
            hour_key = f"{desc.key}_hour"
            if "b_start" in hour_key or "b_end" in hour_key:
                hour_key += "1"
            minute_key = f"{desc.key}_minute"
            if "b_start" in minute_key or "b_end" in minute_key:
                minute_key += "1"

            hour = self.coordinator.data.get(hour_key)
            minute = self.coordinator.data.get(minute_key)
            if hour is None or minute is None:
                return None
            return f"{int(hour):02d}:{int(minute):02d}"

        # Number entity description
        return self.coordinator.data.get(desc.key)
