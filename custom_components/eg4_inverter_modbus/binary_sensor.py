"""Support for EG4 Modbus binary sensors."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    INPUT_REGISTERS,
    HOLDING_REGISTERS,
    EG4ModbusBinarySensorEntityDescription,
    ATTR_MANUFACTURER,
    CONF_ENABLE_READ_SENSORS,
)
from .hub import EG4ModbusHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EG4 binary sensors."""
    hub: EG4ModbusHub = hass.data[DOMAIN][entry.entry_id]
    
    device_info = {
        "identifiers": {(DOMAIN, hub.name)},
        "name": hub.name,
        "manufacturer": ATTR_MANUFACTURER,
        "model": "EG4 Inverter",
    }

    entities = []
    
    # Note: Using CONF_ENABLE_READ_SENSORS to also control optional binary sensors
    enable_read_sensors = entry.options.get(CONF_ENABLE_READ_SENSORS, False)

    # Create sensors from Input Registers
    for description in INPUT_REGISTERS.values():
        if isinstance(description, EG4ModbusBinarySensorEntityDescription):
            is_enabled = description.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            entities.append(EG4BinarySensor(hub, device_info, description, is_enabled))

    # Create sensors from Holding Registers
    for description in HOLDING_REGISTERS.values():
        if isinstance(description, EG4ModbusBinarySensorEntityDescription):
            is_enabled = description.entity_registry_enabled_default
            if enable_read_sensors:
                is_enabled = True
            entities.append(EG4BinarySensor(hub, device_info, description, is_enabled))

    async_add_entities(entities)


class EG4BinarySensor(CoordinatorEntity[EG4ModbusHub], BinarySensorEntity):
    """Representation of an EG4 Modbus binary sensor."""

    entity_description: EG4ModbusBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        hub: EG4ModbusHub,
        device_info: dict,
        description: EG4ModbusBinarySensorEntityDescription,
        enabled_default: bool,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator=hub)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{hub.name}_{description.key}"
        self._attr_name = description.name
        self._attr_entity_enabled_default = enabled_default

    @property
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is None:
            return None
        return bool(val)