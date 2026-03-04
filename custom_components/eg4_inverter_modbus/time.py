"""Support for EG4 Modbus time entities."""
from __future__ import annotations

import logging
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    HOLDING_REGISTERS,
    EG4ModbusTimeEntityDescription,
    ATTR_MANUFACTURER,
    CONF_ENABLE_WRITE_SENSORS,
)
from .hub import EG4ModbusHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EG4 time entities."""
    hub: EG4ModbusHub = hass.data[DOMAIN][entry.entry_id]
    
    device_info = {
        "identifiers": {(DOMAIN, hub.name)},
        "name": hub.name,
        "manufacturer": ATTR_MANUFACTURER,
        "model": "EG4 Inverter",
    }

    entities = []
    
    enable_write_sensors = entry.options.get(CONF_ENABLE_WRITE_SENSORS, False)

    for key, description in HOLDING_REGISTERS.items():
        if isinstance(description, EG4ModbusTimeEntityDescription):
            address = description.address if description.address is not None else key
            if not isinstance(address, int):
                continue
                
            # Calculate the desired state without modifying the global description
            is_enabled = description.entity_registry_enabled_default
            if enable_write_sensors:
                is_enabled = True
            
            # Pass the calculated state to the constructor
            entity = EG4Time(hub, device_info, description, address, is_enabled)
            entities.append(entity)

    async_add_entities(entities)


class EG4Time(CoordinatorEntity[EG4ModbusHub], TimeEntity):
    """Representation of an EG4 Modbus time entity."""

    entity_description: EG4ModbusTimeEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        hub: EG4ModbusHub,
        device_info: dict,
        description: EG4ModbusTimeEntityDescription,
        address: int,
        enabled_default: bool,
    ):
        """Initialize the time entity."""
        super().__init__(coordinator=hub)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{hub.name}_{description.key}"
        self._attr_name = description.name
        self._attr_entity_enabled_default = enabled_default
        self._address = address

    @property
    def native_value(self) -> time | None:
        """Return the native value of the time entity."""
        # Map the general key to the specific hour and minute keys used in hub.py
        hour_key = f"{self.entity_description.key}_hour"
        if "b_start" in hour_key or "b_end" in hour_key:
            hour_key += "1" # Handle the "1" suffix for Peak Shaving B in hub.py
            
        minute_key = f"{self.entity_description.key}_minute"
        if "b_start" in minute_key or "b_end" in minute_key:
            minute_key += "1" # Handle the "1" suffix for Peak Shaving B in hub.py
            
        hour = self.coordinator.data.get(hour_key)
        minute = self.coordinator.data.get(minute_key)

        if hour is None or minute is None:
            return None

        try:
            return time(hour=int(hour), minute=int(minute))
        except ValueError:
            _LOGGER.warning(
                "Invalid time values received for %s: hour=%s, minute=%s",
                self.entity_description.key,
                hour,
                minute,
            )
            return None

    async def async_set_value(self, value: time) -> None:
        """Change the time."""
        # Modbus format: high byte is minute, low byte is hour
        register_value = (value.minute << 8) | value.hour
        
        success = await self.hass.async_add_executor_job(
            self.coordinator.write_register, self._address, register_value
        )

        if success:
            hour_key = f"{self.entity_description.key}_hour"
            if "b_start" in hour_key or "b_end" in hour_key:
                hour_key += "1"
                
            minute_key = f"{self.entity_description.key}_minute"
            if "b_start" in minute_key or "b_end" in minute_key:
                minute_key += "1"
                
            self.coordinator.data[hour_key] = value.hour
            self.coordinator.data[minute_key] = value.minute
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
