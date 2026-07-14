"""Test Modbus Hub for EG4 Inverter Modbus."""

from unittest.mock import MagicMock, patch
import pytest

from homeassistant.core import HomeAssistant
from pymodbus.exceptions import ConnectionException

from custom_components.eg4_inverter_modbus.hub import CustomPayloadDecoder, EG4ModbusHub


def test_custom_payload_decoder():
    """Test the CustomPayloadDecoder helper class."""
    registers = [0x1234, 0x5678, 0x8001, 0xFFFF]
    decoder = CustomPayloadDecoder(registers)
    
    # 16bit uint
    assert decoder.decode_16bit_uint() == 0x1234
    
    # 16bit int (signed)
    assert decoder.decode_16bit_int() == 0x5678
    
    # Skip one register
    decoder.skip_registers(1)
    
    # 0xFFFF is -1 in 16bit signed int representation
    assert decoder.decode_16bit_int() == -1
    
    # Check IndexError when out of range
    with pytest.raises(IndexError):
        decoder.decode_16bit_uint()
        
    # Test 32bit decoding (registers in low word, high word format)
    registers2 = [0x5678, 0x1234, 0x0001, 0x8000]
    decoder2 = CustomPayloadDecoder(registers2)
    # 0x12345678
    assert decoder2.decode_32bit_uint() == 0x12345678
    # 0x80000001 is -2147483647 signed
    assert decoder2.decode_32bit_int() == -2147483647


async def test_hub_pymodbus_kwargs(hass: HomeAssistant):
    """Test that the hub correctly detects pymodbus kwarg names."""
    with patch("custom_components.eg4_inverter_modbus.hub.SafeModbusTcpClient") as mock_client:
        hub = EG4ModbusHub(hass, "Test Hub", "10.0.0.100", 502, 5, 10)
        assert hub._device_id == 5
        # Ensure one of the valid unit keyword arguments is parsed
        assert any(k in hub._kwargs for k in ("slave", "unit", "device_id"))


async def test_hub_discover_batteries(hass: HomeAssistant, mock_modbus_client):
    """Test battery discovery register scanning."""
    hub = EG4ModbusHub(hass, "Test Hub", "10.0.0.100", 502, 1, 10)
    
    # Case 1: No batteries discovered (reads return error)
    mock_modbus_client.read_input_registers.return_value = MagicMock(
        isError=MagicMock(return_value=True)
    )
    hub.discover_batteries()
    assert hub.battery_count == 0
    
    # Case 2: 2 batteries discovered
    def mock_read_input_registers(address, count, **kwargs):
        # Battery 1 at 5000: returns valid marker 0xC002 at index 2
        if address == 5000:
            regs = [0] * 30
            regs[2] = 0xC002
            return MagicMock(isError=MagicMock(return_value=False), registers=regs)
        # Battery 2 at 5030: returns valid capacity at index 3
        elif address == 5030:
            regs = [0] * 30
            regs[3] = 100
            return MagicMock(isError=MagicMock(return_value=False), registers=regs)
        # Battery 3 at 5060: fails/out of range
        else:
            return MagicMock(isError=MagicMock(return_value=True))
            
    mock_modbus_client.read_input_registers.side_effect = mock_read_input_registers
    hub.discover_batteries()
    assert hub.battery_count == 2


async def test_hub_write_register(hass: HomeAssistant, mock_modbus_client):
    """Test hub write_register and write_masked_register (RMW)."""
    hub = EG4ModbusHub(hass, "Test Hub", "10.0.0.100", 502, 1, 10)
    
    # 1. Test standard successful write
    mock_modbus_client.write_register.return_value = MagicMock(isError=MagicMock(return_value=False))
    assert hub.write_register(100, 200) is True
    mock_modbus_client.write_register.assert_called_with(address=100, value=200, **hub._kwargs)
    
    # 2. Test failed write (returns error response)
    mock_modbus_client.write_register.return_value = MagicMock(isError=MagicMock(return_value=True))
    assert hub.write_register(100, 200) is False
    
    # 3. Test failed write due to connection exception
    mock_modbus_client.write_register.side_effect = ConnectionException("Modbus connection lost")
    assert hub.write_register(100, 200) is False
    
    # Reset side effect
    mock_modbus_client.write_register.side_effect = None
    
    # 4. Test write_masked_register (Read-Modify-Write)
    # Mask = 0x00F0, value = 5 -> (5 << 4) = 0x0050. Old register value = 0x1234
    # Expected: (0x1234 & ~0x00F0) | 0x0050 = 0x1204 | 0x0050 = 0x1254
    mock_modbus_client.read_holding_registers.return_value = MagicMock(
        isError=MagicMock(return_value=False),
        registers=[0x1234]
    )
    mock_modbus_client.write_register.return_value = MagicMock(isError=MagicMock(return_value=False))
    
    assert hub.write_masked_register(150, 5, 0x00F0) is True
    mock_modbus_client.write_register.assert_called_with(address=150, value=0x1254, **hub._kwargs)


async def test_hub_sync_update_data_and_spike_filter(hass: HomeAssistant, mock_modbus_client):
    """Test hub syncing data updates and spike filtering logic."""
    hub = EG4ModbusHub(hass, "Test Hub", "10.0.0.100", 502, 1, 10)
    hub.battery_count = 1
    
    # Populate registers with standard mock data
    def mock_read(address, count, **kwargs):
        # Battery block 5000: capacity=100 (reg 3), voltage=51.2V (reg 8), current=10.0A (reg 9), soc=80 (reg 10)
        if address == 5000:
            regs = [0] * 30
            regs[3] = 100
            regs[8] = 5120
            regs[9] = 1000
            regs[10] = (100 << 8) | 80
            return MagicMock(isError=MagicMock(return_value=False), registers=regs)
        # Block 1 (0-39): PV1 voltage = 300V (reg 1), battery SoC = 80 (reg 5), PV1 power = 1000 (reg 7)
        elif address == 0:
            regs = [0] * 40
            regs[0] = 2
            regs[1] = 3000
            regs[5] = (100 << 8) | 80
            regs[7] = 1000
            return MagicMock(isError=MagicMock(return_value=False), registers=regs)
        else:
            return MagicMock(isError=MagicMock(return_value=False), registers=[0] * count)
            
    mock_modbus_client.read_input_registers.side_effect = mock_read
    
    # Baseline update
    data1 = hub._sync_update_data()
    assert data1["voltage_pv1"] == 300.0
    assert data1["battery_soc"] == 80
    assert data1["power_pv1"] == 1000
    assert data1["power_pv_total"] == 1000
    
    # Test spike filter on voltage_pv1 (300V -> 500V is a diff of 200, which is > 40)
    def mock_read_spike(address, count, **kwargs):
        if address == 0:
            regs = [0] * 40
            regs[0] = 2
            regs[1] = 5000 # spiked pv1 volt
            regs[5] = (100 << 8) | 80
            regs[7] = 1000
            return MagicMock(isError=MagicMock(return_value=False), registers=regs)
        else:
            return mock_read(address, count, **kwargs)
            
    mock_modbus_client.read_input_registers.side_effect = mock_read_spike
    
    # Poll 1 (Spike): should reject and keep old baseline value (300.0)
    data2 = hub._sync_update_data()
    assert data2["voltage_pv1"] == 300.0
    assert hub._consecutive_rejects["voltage_pv1"] == 1
    
    # Poll 2 (Spike): should reject again and keep old baseline value (300.0)
    data3 = hub._sync_update_data()
    assert data3["voltage_pv1"] == 300.0
    assert hub._consecutive_rejects["voltage_pv1"] == 2
    
    # Poll 3 (Spike): persistent spike, should accept the new value (500.0)
    data4 = hub._sync_update_data()
    assert data4["voltage_pv1"] == 500.0
    assert hub._consecutive_rejects["voltage_pv1"] == 0
