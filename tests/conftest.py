"""Fixtures for EG4 Inverter Modbus integration tests."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eg4_inverter_modbus.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_modbus_client():
    """Mock the SafeModbusTcpClient class."""
    with patch("custom_components.eg4_inverter_modbus.hub.SafeModbusTcpClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Setup context manager return value to make with self._client work
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None

        # Setup standard mock behaviors
        mock_client.is_socket_open.return_value = True
        mock_client.connect.return_value = True
        
        # Read/write responses default to success with empty/zeroed registers
        mock_client.read_input_registers.return_value = MagicMock(
            isError=MagicMock(return_value=False), 
            registers=[0] * 100
        )
        mock_client.read_holding_registers.return_value = MagicMock(
            isError=MagicMock(return_value=False), 
            registers=[0] * 100
        )
        mock_client.write_register.return_value = MagicMock(
            isError=MagicMock(return_value=False)
        )
        
        yield mock_client


@pytest.fixture(autouse=True)
def mock_integration_loader(hass):
    """Mock the homeassistant loader to return our integration."""
    from homeassistant.loader import Integration
    import custom_components.eg4_inverter_modbus as integration_module
    import os
    import pathlib
    
    pkg_dir = os.path.dirname(integration_module.__file__)
    mock_integration = Integration(
        hass,
        "custom_components.eg4_inverter_modbus",
        pathlib.Path(pkg_dir),
        {
            "domain": "eg4_inverter_modbus",
            "name": "EG4 Inverter Modbus",
            "version": "0.0.5",
        }
    )
    # Populate cache to handle direct loader imports across homeassistant helper modules
    hass.data.setdefault("integrations", {})["eg4_inverter_modbus"] = mock_integration
    
    with patch("homeassistant.loader.async_get_integration", new=AsyncMock(return_value=mock_integration)):
        yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Inverter",
        data={
            CONF_NAME: "Test Inverter",
        },
        options={
            CONF_HOST: "10.0.0.100",
            CONF_PORT: 502,
            "slave": 1,
            "scan_interval": 10,
            "enable_all_read_sensors": False,
            "enable_write_sensors": False,
        },
        entry_id="test_entry_id",
        unique_id="eg4_inverter_modbus_Test Inverter",
    )
