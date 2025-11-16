"""Support for EG4 Modbus select entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    HOLDING_REGISTERS,
    EG4ModbusSelectEntityDescription,
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
    """Set up the EG4 select entities."""
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
        if isinstance(description, EG4ModbusSelectEntityDescription):
            # Calculate the desired state without modifying the global description
            is_enabled = description.entity_registry_enabled_default
            if enable_write_sensors:
                is_enabled = True

            # Pass the calculated state to the constructor
            entity = EG4Select(hub, device_info, description, address, is_enabled)
            entities.append(entity)

    async_add_entities(entities)


class EG4Select(CoordinatorEntity[EG4ModbusHub], SelectEntity):
    """Representation of an EG4 Modbus select entity."""

    entity_description: EG4ModbusSelectEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        hub: EG4ModbusHub,
        device_info: dict,
        description: EG4ModbusSelectEntityDescription,
        address: int,
        enabled_default: bool,  # <-- Add this argument
    ):
        """Initialize the select entity."""
        super().__init__(coordinator=hub)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{hub.name}_{description.key}"
        self._attr_name = description.name
        self._attr_entity_enabled_default = enabled_default  # <-- Use the argument
        self._address = address

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is None:
            return None
        
        try:
            return self.entity_description.options[int(val)]
        except (ValueError, IndexError):
            s_val = str(val)
            if s_val in self.entity_description.options:
                return s_val
            _LOGGER.warning(f"Value '{val}' is not a valid index or option for {self.name}")
            return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            index = self.entity_description.options.index(option)
            if await self.hass.async_add_executor_job(
                self.coordinator.write_register, self._address, index
            ):
                self.coordinator.data[self.entity_description.key] = index
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
        except ValueError:
            _LOGGER.error(f"'{option}' is not a valid option for {self.name}")
