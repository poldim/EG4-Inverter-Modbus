"""Support for EG4 Modbus number entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    HOLDING_REGISTERS,
    EG4ModbusNumberEntityDescription,
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
    """Set up the EG4 number entities."""
    hub: EG4ModbusHub = hass.data[DOMAIN][entry.entry_id]
    
    device_info = {
        "identifiers": {(DOMAIN, hub.name)},
        "name": hub.name,
        "manufacturer": ATTR_MANUFACTURER,
        "model": "EG4 Inverter",
    }

    entities = []
    
    enable_write_sensors = entry.options.get(CONF_ENABLE_WRITE_SENSORS, False)

    for address, description in HOLDING_REGISTERS.items():
        if isinstance(description, EG4ModbusNumberEntityDescription):
            # Calculate the desired state without modifying the global description
            is_enabled = description.entity_registry_enabled_default
            if enable_write_sensors:
                is_enabled = True
            
            # Pass the calculated state to the constructor
            entity = EG4Number(hub, device_info, description, address, is_enabled)
            entities.append(entity)

    async_add_entities(entities)


class EG4Number(CoordinatorEntity[EG4ModbusHub], NumberEntity):
    """Representation of an EG4 Modbus number entity."""

    entity_description: EG4ModbusNumberEntityDescription
    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True

    def __init__(
        self,
        hub: EG4ModbusHub,
        device_info: dict,
        description: EG4ModbusNumberEntityDescription,
        address: int,
        enabled_default: bool,  # <-- Add this argument
    ):
        """Initialize the number entity."""
        super().__init__(coordinator=hub)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{hub.name}_{description.key}"
        self._attr_name = description.name
        self._attr_entity_enabled_default = enabled_default  # <-- Use the argument
        self._address = address

    @property
    def native_value(self) -> float | None:
        """Return the state of the entity."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is None:
            return None
        return float(val)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        scaled_value = int(value / self.entity_description.scale)
        if await self.hass.async_add_executor_job(
            self.coordinator.write_register, self._address, scaled_value
        ):
            self.coordinator.data[self.entity_description.key] = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
