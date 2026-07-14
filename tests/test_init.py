"""Test initialization for EG4 Inverter Modbus."""

from unittest.mock import MagicMock, patch
import pytest

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eg4_inverter_modbus import (
    _update_entity_registry,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
    PLATFORMS,
)
from custom_components.eg4_inverter_modbus.const import DOMAIN
from custom_components.eg4_inverter_modbus.hub import EG4ModbusHub


async def test_setup_unload_entry(hass: HomeAssistant, mock_modbus_client, mock_config_entry):
    """Test setting up and unloading an entry."""
    mock_config_entry.add_to_hass(hass)
    
    # Mock battery discovery to run instantly without making real calls
    with patch("custom_components.eg4_inverter_modbus.hub.EG4ModbusHub.discover_batteries") as mock_discover:
        with patch.object(hass.config_entries, "async_forward_entry_setups", return_value=True) as mock_forward:
            assert await async_setup_entry(hass, mock_config_entry) is True
            assert mock_discover.called
            mock_forward.assert_called_once_with(mock_config_entry, PLATFORMS)
            
            # Verify hub is created and stored in hass
            hub = hass.data[DOMAIN][mock_config_entry.entry_id]
            assert isinstance(hub, EG4ModbusHub)
            assert hub.name == mock_config_entry.data[CONF_NAME]
            
            # Test unloading the entry
            with patch.object(hass.config_entries, "async_unload_platforms", return_value=True) as mock_unload:
                with patch.object(hub, "close") as mock_close:
                    assert await async_unload_entry(hass, mock_config_entry) is True
                    mock_unload.assert_called_once_with(mock_config_entry, PLATFORMS)
                    assert mock_close.called
                    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_update_options_listener(hass: HomeAssistant, mock_config_entry):
    """Test options update listener reloads the integration."""
    mock_config_entry.add_to_hass(hass)
    
    with patch.object(hass.config_entries, "async_reload", return_value=True) as mock_reload:
        await async_update_options(hass, mock_config_entry)
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


async def test_update_entity_registry_toggles(hass: HomeAssistant, mock_modbus_client, mock_config_entry):
    """Test _update_entity_registry updates disabled_by field based on checkboxes."""
    mock_config_entry.add_to_hass(hass)
    
    registry = er.async_get(hass)
    
    # Pre-populate registry with a sensor defaulting to enabled
    entry_enabled = registry.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id=f"{mock_config_entry.data[CONF_NAME]}_power_pv1",
        config_entry=mock_config_entry,
    )
    
    # Pre-populate registry with a number defaulting to disabled
    entry_disabled = registry.async_get_or_create(
        domain="number",
        platform=DOMAIN,
        unique_id=f"{mock_config_entry.data[CONF_NAME]}_setting_battery_nominal_voltage",
        config_entry=mock_config_entry,
        disabled_by=er.RegistryEntryDisabler.INTEGRATION,
    )
    
    # Store mocked hub in hass.data as required by _update_entity_registry
    hub = EG4ModbusHub(hass, mock_config_entry.data[CONF_NAME], "10.0.0.100", 502, 1, 10)
    hass.data[DOMAIN] = {mock_config_entry.entry_id: hub}
    
    # 1. Enable both checkboxes: both entities should end up enabled
    new_options = dict(mock_config_entry.options)
    new_options.update({
        "enable_all_read_sensors": True,
        "enable_write_sensors": True,
    })
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
    
    await _update_entity_registry(hass, mock_config_entry)
    
    entity_enabled = registry.async_get(entry_enabled.entity_id)
    entity_disabled = registry.async_get(entry_disabled.entity_id)
    assert entity_enabled.disabled_by is None
    assert entity_disabled.disabled_by is None
    
    # 2. Disable both checkboxes: entry_disabled should revert to disabled, entry_enabled stays enabled
    new_options.update({
        "enable_all_read_sensors": False,
        "enable_write_sensors": False,
    })
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
    
    await _update_entity_registry(hass, mock_config_entry)
    
    entity_enabled = registry.async_get(entry_enabled.entity_id)
    entity_disabled = registry.async_get(entry_disabled.entity_id)
    assert entity_enabled.disabled_by is None
    assert entity_disabled.disabled_by == er.RegistryEntryDisabler.INTEGRATION
