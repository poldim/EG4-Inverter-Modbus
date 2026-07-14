"""Test platform entities for EG4 Inverter Modbus."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from homeassistant.core import HomeAssistant

from custom_components.eg4_inverter_modbus.binary_sensor import EG4BinarySensor
from custom_components.eg4_inverter_modbus.const import (
    EG4ModbusBinarySensorEntityDescription,
    EG4ModbusNumberEntityDescription,
    EG4ModbusSelectEntityDescription,
    EG4ModbusSensorEntityDescription,
    EG4ModbusTimeEntityDescription,
)
from custom_components.eg4_inverter_modbus.hub import EG4ModbusHub
from custom_components.eg4_inverter_modbus.number import EG4Number
from custom_components.eg4_inverter_modbus.select import EG4Select
from custom_components.eg4_inverter_modbus.sensor import EG4Sensor
from custom_components.eg4_inverter_modbus.time import EG4Time


@pytest.fixture
def test_hub(hass: HomeAssistant, mock_modbus_client):
    """Fixture for EG4ModbusHub with mock client."""
    hub = EG4ModbusHub(hass, "Test Inverter", "10.0.0.100", 502, 1, 10)
    hub.data = {}
    hub.async_request_refresh = AsyncMock()
    return hub


async def test_sensor_entity(test_hub):
    """Test Sensor entity native_value extraction."""
    desc = EG4ModbusSensorEntityDescription(
        key="voltage_pv1",
        name="PV1 Voltage",
        native_unit_of_measurement="V",
    )
    device_info = {}
    sensor = EG4Sensor(test_hub, device_info, desc, True)
    
    # Check default/missing value
    assert sensor.native_value is None
    
    # Set data in hub and verify state mapping
    test_hub.data["voltage_pv1"] = 345.2
    assert sensor.native_value == 345.2


async def test_binary_sensor_entity(test_hub):
    """Test Binary Sensor state mapping."""
    desc = EG4ModbusBinarySensorEntityDescription(
        key="afci_alarm_ch1",
        name="AFCI Alarm Ch1",
    )
    device_info = {}
    binary_sensor = EG4BinarySensor(test_hub, device_info, desc, True)
    
    # Missing value
    assert binary_sensor.is_on is None
    
    # On state
    test_hub.data["afci_alarm_ch1"] = 1
    assert binary_sensor.is_on is True
    
    # Off state
    test_hub.data["afci_alarm_ch1"] = 0
    assert binary_sensor.is_on is False


async def test_number_entity(test_hub, mock_modbus_client):
    """Test Number entity value mapping and setting."""
    desc = EG4ModbusNumberEntityDescription(
        key="setting_voltage_charge_ref",
        name="Charge Voltage Reference",
        scale=0.1,
    )
    device_info = {}
    number = EG4Number(test_hub, device_info, desc, 64, True)
    number.hass = MagicMock()
    number.hass.async_add_executor_job = AsyncMock(return_value=True)
    number.async_write_ha_state = MagicMock()
    
    # Read value
    test_hub.data["setting_voltage_charge_ref"] = 54.0
    assert number.native_value == 54.0
    
    # Set value (e.g. 54.0 / 0.1 = 540)
    # Since bit_mask is None, it should call write_register on hub
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    number.hass.async_add_executor_job.side_effect = mock_executor
    
    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await number.async_set_native_value(54.0)
        mock_write.assert_called_once_with(64, 540)
        
        # Verify state is updated locally immediately
        assert test_hub.data["setting_voltage_charge_ref"] == 54.0


async def test_number_entity_masked(test_hub, mock_modbus_client):
    """Test Number entity with bit mask RMW operations."""
    desc = EG4ModbusNumberEntityDescription(
        key="setting_percent_charge_power",
        name="Max Charge Power Percent",
        bit_mask=0xFF00,
        scale=1.0,
    )
    device_info = {}
    number = EG4Number(test_hub, device_info, desc, 70, True)
    number.hass = MagicMock()
    number.hass.async_add_executor_job = AsyncMock(return_value=True)
    number.async_write_ha_state = MagicMock()
    
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    number.hass.async_add_executor_job.side_effect = mock_executor
    
    with patch.object(test_hub, "write_masked_register", return_value=True) as mock_masked_write:
        await number.async_set_native_value(80.0)
        mock_masked_write.assert_called_once_with(70, 80, 0xFF00)


async def test_select_entity(test_hub):
    """Test Select entity option indexing and setting."""
    desc = EG4ModbusSelectEntityDescription(
        key="setting_pv_input_model",
        name="PV Input Model",
        options=["Independent", "Parallel", "Parallel & Independent"],
        option_dict={
            0: "Independent",
            1: "Parallel",
            2: "Parallel & Independent",
        }
    )
    device_info = {}
    select = EG4Select(test_hub, device_info, desc, 80, True)
    select.hass = MagicMock()
    select.hass.async_add_executor_job = AsyncMock(return_value=True)
    select.async_write_ha_state = MagicMock()
    
    # Read option index 1 -> Parallel
    test_hub.data["setting_pv_input_model"] = 1
    assert select.current_option == "Parallel"
    
    # Set option Parallel & Independent -> index 2
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    select.hass.async_add_executor_job.side_effect = mock_executor
    
    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await select.async_select_option("Parallel & Independent")
        mock_write.assert_called_once_with(80, 2)
        assert test_hub.data["setting_pv_input_model"] == 2


async def test_time_entity_peak_shaving_logic(test_hub):
    """Test Time entity peak shaving hour/minute parsing and format encoding."""
    desc = EG4ModbusTimeEntityDescription(
        key="setting_peak_shaving_a_start",
        name="Peak Shaving A Start Time",
    )
    device_info = {}
    time_entity = EG4Time(test_hub, device_info, desc, 209, True)
    time_entity.hass = MagicMock()
    time_entity.hass.async_add_executor_job = AsyncMock(return_value=True)
    time_entity.async_write_ha_state = MagicMock()
    
    # Check default/missing
    assert time_entity.native_value is None
    
    # Read normal time
    test_hub.data["setting_peak_shaving_a_start_hour"] = 8
    test_hub.data["setting_peak_shaving_a_start_minute"] = 30
    assert time_entity.native_value == datetime.time(8, 30)
    
    # Set time: 14:45 -> (45 << 8) | 14 = 0x2D0E = 11534
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    time_entity.hass.async_add_executor_job.side_effect = mock_executor
    
    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await time_entity.async_set_value(datetime.time(14, 45))
        mock_write.assert_called_once_with(209, 11534)
        assert test_hub.data["setting_peak_shaving_a_start_hour"] == 14
        assert test_hub.data["setting_peak_shaving_a_start_minute"] == 45
        
    # Check B Start/End time logic (requires "1" suffix mapping in hub.py)
    desc_b = EG4ModbusTimeEntityDescription(
        key="setting_peak_shaving_b_end",
        name="Peak Shaving B End Time",
    )
    time_entity_b = EG4Time(test_hub, device_info, desc_b, 212, True)
    time_entity_b.hass = MagicMock()
    time_entity_b.hass.async_add_executor_job = AsyncMock(return_value=True)
    time_entity_b.hass.async_add_executor_job.side_effect = mock_executor
    time_entity_b.async_write_ha_state = MagicMock()
    
    test_hub.data["setting_peak_shaving_b_end_hour1"] = 23
    test_hub.data["setting_peak_shaving_b_end_minute1"] = 15
    assert time_entity_b.native_value == datetime.time(23, 15)
    
    with patch.object(test_hub, "write_register", return_value=True) as mock_write_b:
        await time_entity_b.async_set_value(datetime.time(1, 5))
        mock_write_b.assert_called_once_with(212, 1281) # (5 << 8) | 1 = 1281
        assert test_hub.data["setting_peak_shaving_b_end_hour1"] == 1
        assert test_hub.data["setting_peak_shaving_b_end_minute1"] == 5
