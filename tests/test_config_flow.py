"""Test config flow for EG4 Inverter Modbus."""

from unittest.mock import patch
import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eg4_inverter_modbus.const import DOMAIN


async def test_user_flow_show_form(hass: HomeAssistant):
    """Test that the user step displays the setup form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_flow_success(hass: HomeAssistant):
    """Test standard successful user setup flow."""
    # Mock entry setup to prevent actual background execution
    with patch(
        "custom_components.eg4_inverter_modbus.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        
        # Submit valid input data
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "EG4 Test Inverter",
                CONF_HOST: "10.0.0.50",
                CONF_PORT: 502,
                "slave": 1,
                "scan_interval": 15,
                "enable_all_read_sensors": True,
                "enable_write_sensors": False,
            },
        )
        
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "EG4 Test Inverter"
        assert result["data"] == {CONF_NAME: "EG4 Test Inverter"}
        assert result["options"] == {
            CONF_HOST: "10.0.0.50",
            CONF_PORT: 502,
            "slave": 1,
            "scan_interval": 15,
            "enable_all_read_sensors": True,
            "enable_write_sensors": False,
        }
        
        await hass.async_block_till_done()
        assert len(mock_setup_entry.mock_calls) == 1


async def test_user_flow_duplicate(hass: HomeAssistant):
    """Test that config flow aborts if unique ID already exists."""
    # Create a pre-existing config entry with the same name/unique ID
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="EG4 Test Inverter",
        data={CONF_NAME: "EG4 Test Inverter"},
        unique_id="eg4_inverter_modbus_EG4 Test Inverter",
    )
    entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "EG4 Test Inverter",
            CONF_HOST: "10.0.0.50",
            CONF_PORT: 502,
            "slave": 1,
        },
    )
    
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant):
    """Test options flow configuration updates."""
    # Pre-add config entry with original options
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="EG4 Test Inverter",
        data={CONF_NAME: "EG4 Test Inverter"},
        options={
            CONF_HOST: "10.0.0.50",
            CONF_PORT: 502,
            "slave": 1,
            "scan_interval": 10,
            "enable_all_read_sensors": False,
            "enable_write_sensors": False,
        },
    )
    entry.add_to_hass(hass)
    
    # Initialize options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"
    
    # Configure and save options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "10.0.0.60",
            CONF_PORT: 503,
            "slave": 2,
            "scan_interval": 20,
            "enable_all_read_sensors": True,
            "enable_write_sensors": True,
        },
    )
    
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"] == {
        CONF_HOST: "10.0.0.60",
        CONF_PORT: 503,
        "slave": 2,
        "scan_interval": 20,
        "enable_all_read_sensors": True,
        "enable_write_sensors": True,
    }
