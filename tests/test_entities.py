"""Test platform entities for EG4 Inverter Modbus."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

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
    assert sensor.entity_registry_enabled_default is True
    sensor_disabled = EG4Sensor(test_hub, device_info, desc, False)
    assert sensor_disabled.entity_registry_enabled_default is False
    
    # Check default/missing value
    assert sensor.native_value is None
    
    # Set data in hub and verify state mapping
    test_hub.data["voltage_pv1"] = 345.2
    assert sensor.native_value == 345.2


async def test_battery_sensor_entity_naming(test_hub):
    """Test dynamic Battery Sensor naming does not duplicate Battery prefix."""
    from dataclasses import replace
    from custom_components.eg4_inverter_modbus.const import BATTERY_SENSOR_DEFINITIONS

    # Verify BATTERY_SENSOR_DEFINITIONS names do not have 'Battery' in them
    assert "capacity_system" not in BATTERY_SENSOR_DEFINITIONS
    for key, desc in BATTERY_SENSOR_DEFINITIONS.items():
        assert not desc.name.startswith("Battery"), f"{key} name '{desc.name}' should not start with 'Battery'"

    # Simulate sensor setup for battery 1
    battery_num = 1
    prefix = f"battery{battery_num:02d}"
    base_desc = BATTERY_SENSOR_DEFINITIONS["capacity_pack"]
    new_key = base_desc.key.format(prefix)
    new_name = base_desc.name.format(battery_num) if "{}" in base_desc.name else base_desc.name
    desc = replace(base_desc, key=new_key, name=new_name)

    dev_info = test_hub.get_device_info(desc.key, desc.entity_category)
    sensor = EG4Sensor(test_hub, dev_info, desc, True)

    assert sensor.has_entity_name is True
    assert sensor.name == "Capacity"
    assert dev_info["name"] == "Test Inverter Battery 1"
    assert sensor.unique_id == "Test Inverter_battery01_capacity_pack"


async def test_binary_sensor_entity(test_hub):
    """Test Binary Sensor state mapping."""
    desc = EG4ModbusBinarySensorEntityDescription(
        key="afci_alarm_ch1",
        name="AFCI Alarm Ch1",
    )
    device_info = {}
    binary_sensor = EG4BinarySensor(test_hub, device_info, desc, True)
    assert binary_sensor.entity_registry_enabled_default is True
    binary_sensor_disabled = EG4BinarySensor(test_hub, device_info, desc, False)
    assert binary_sensor_disabled.entity_registry_enabled_default is False
    
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
    assert number.entity_registry_enabled_default is True
    number_disabled = EG4Number(test_hub, device_info, desc, 64, False)
    assert number_disabled.entity_registry_enabled_default is False
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
    assert select.entity_registry_enabled_default is True
    select_disabled = EG4Select(test_hub, device_info, desc, 80, False)
    assert select_disabled.entity_registry_enabled_default is False
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
    assert time_entity.entity_registry_enabled_default is True
    time_entity_disabled = EG4Time(test_hub, device_info, desc, 209, False)
    assert time_entity_disabled.entity_registry_enabled_default is False
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


async def test_battery_capacity_registers(test_hub):
    """Test Register 97 name and Register 147 number entity configuration."""
    from custom_components.eg4_inverter_modbus.const import INPUT_REGISTERS, HOLDING_REGISTERS, EG4ModbusNumberEntityDescription

    # Register 97: Battery Capacity Total System
    desc_97 = INPUT_REGISTERS[97]
    assert desc_97.name == "Battery Capacity Total System"
    assert desc_97.key == "battery_capacity_ah"
    assert desc_97.icon == "mdi:battery"

    # Register 147: Battery Capacity Unmatched Override
    desc_147 = HOLDING_REGISTERS[147]
    assert isinstance(desc_147, EG4ModbusNumberEntityDescription)
    assert desc_147.name == "Battery Capacity Unmatched Override"
    from homeassistant.helpers.entity import EntityCategory
    assert desc_147.entity_category == EntityCategory.CONFIG
    assert desc_147.native_unit_of_measurement == "Ah"
    assert desc_147.native_min_value == 0
    assert desc_147.native_max_value == 10000
    assert desc_147.native_step == 1
    assert desc_147.scale == 1.0
    assert desc_147.icon == "mdi:battery"

    # AFCI current sensors
    for reg in (140, 141, 142, 143):
        assert INPUT_REGISTERS[reg].icon == "mdi:flash"

    # Device info check for Inverter Settings
    dev_info = test_hub.get_device_info(desc_147.key, desc_147.entity_category)
    assert dev_info["name"] == "Test Inverter Inverter Settings"

    # Number entity creation and value read/write
    entity = EG4Number(test_hub, dev_info, desc_147, 147, True)
    entity.hass = MagicMock()
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    entity.async_write_ha_state = MagicMock()

    test_hub.data["setting_battery_capacity_unmatched_override"] = 560
    assert entity.native_value == 560.0

    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await entity.async_set_native_value(600)
        mock_write.assert_called_once_with(147, 600)
        assert test_hub.data["setting_battery_capacity_unmatched_override"] == 600


async def test_ac_charge_rate_number_entity(test_hub):
    """Test Register 66 AC Charge Rate number entity configuration in kW."""
    from homeassistant.const import UnitOfPower
    from custom_components.eg4_inverter_modbus.const import HOLDING_REGISTERS, EG4ModbusNumberEntityDescription

    desc_66 = HOLDING_REGISTERS[66]
    assert isinstance(desc_66, EG4ModbusNumberEntityDescription)
    assert desc_66.name == "AC Charge Rate"
    assert desc_66.key == "setting_ac_charge_rate"
    assert desc_66.native_unit_of_measurement == UnitOfPower.KILO_WATT
    assert desc_66.scale == 0.1
    assert desc_66.native_min_value == 0
    assert desc_66.native_max_value == 25.0

    # Device info check for Inverter Settings
    dev_info = test_hub.get_device_info(desc_66.key, desc_66.entity_category)
    assert dev_info["name"] == "Test Inverter Inverter Settings"

    # Number entity creation and value read/write
    entity = EG4Number(test_hub, dev_info, desc_66, 66, True)
    entity.hass = MagicMock()
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    entity.async_write_ha_state = MagicMock()

    # 80 raw -> 8.0 kW
    test_hub.data["setting_ac_charge_rate"] = 80 / 10.0
    assert entity.native_value == 8.0

    # Setting 8 kW writes 80 to register 66
    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await entity.async_set_native_value(8.0)
        mock_write.assert_called_once_with(66, 80)
        assert test_hub.data["setting_ac_charge_rate"] == 8.0


async def test_grid_export_power_limit_number_entity(test_hub):
    """Test Register 103 Grid Export Power Limit number entity configuration in kW."""
    from homeassistant.const import UnitOfPower
    from custom_components.eg4_inverter_modbus.const import HOLDING_REGISTERS, EG4ModbusNumberEntityDescription

    desc_103 = HOLDING_REGISTERS[103]
    assert isinstance(desc_103, EG4ModbusNumberEntityDescription)
    assert desc_103.name == "Grid Export Power Limit"
    assert desc_103.key == "setting_grid_export_power_limit"
    assert desc_103.native_unit_of_measurement == UnitOfPower.KILO_WATT
    assert desc_103.scale == 0.1
    assert desc_103.native_min_value == 0.0
    assert desc_103.native_max_value == 25.0
    assert desc_103.native_step == 0.1

    # Device info check for Inverter Settings
    dev_info = test_hub.get_device_info(desc_103.key, desc_103.entity_category)
    assert dev_info["name"] == "Test Inverter Inverter Settings"

    # Number entity creation and value read/write
    entity = EG4Number(test_hub, dev_info, desc_103, 103, True)
    entity.hass = MagicMock()
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    entity.async_write_ha_state = MagicMock()

    # 80 raw -> 8.0 kW
    test_hub.data["setting_grid_export_power_limit"] = 80 / 10.0
    assert entity.native_value == 8.0

    # Setting 8 kW writes 80 to register 103
    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await entity.async_set_native_value(8.0)
        mock_write.assert_called_once_with(103, 80)
        assert test_hub.data["setting_grid_export_power_limit"] == 8.0



async def test_ac_charge_time_slots_and_sporadic_charge(test_hub):
    """Test AC Charge time slots (T1, T2, T3) and sporadic charge select entity."""
    from custom_components.eg4_inverter_modbus.const import HOLDING_REGISTERS

    # 1. Verify AC Charge Time Slots (registers 68-73) descriptions
    time_slots = [
        (68, "setting_ac_charge_t1_start", "AC Charge T1 Start Time", "mdi:clock-start"),
        (69, "setting_ac_charge_t1_end", "AC Charge T1 End Time", "mdi:clock-end"),
        (70, "setting_ac_charge_t2_start", "AC Charge T2 Start Time", "mdi:clock-start"),
        (71, "setting_ac_charge_t2_end", "AC Charge T2 End Time", "mdi:clock-end"),
        (72, "setting_ac_charge_t3_start", "AC Charge T3 Start Time", "mdi:clock-start"),
        (73, "setting_ac_charge_t3_end", "AC Charge T3 End Time", "mdi:clock-end"),
    ]

    for addr, key, name, icon in time_slots:
        desc = HOLDING_REGISTERS[addr]
        assert isinstance(desc, EG4ModbusTimeEntityDescription)
        assert desc.key == key
        assert desc.name == name
        assert desc.address == addr
        from homeassistant.helpers.entity import EntityCategory
        assert desc.entity_category == EntityCategory.CONFIG
        assert desc.entity_registry_enabled_default is True
        assert desc.icon == icon

        # Device info maps setting_* to Inverter Settings
        dev_info = test_hub.get_device_info(desc.key, desc.entity_category)
        assert dev_info["name"] == "Test Inverter Inverter Settings"

    # Test reading and writing T1 Start time (reg 68)
    desc_t1_start = HOLDING_REGISTERS[68]
    dev_info_t1 = test_hub.get_device_info(desc_t1_start.key, desc_t1_start.entity_category)
    entity_t1_start = EG4Time(test_hub, dev_info_t1, desc_t1_start, 68, True)
    entity_t1_start.hass = MagicMock()
    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)
    entity_t1_start.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    entity_t1_start.async_write_ha_state = MagicMock()

    # Reading hour 1, minute 0
    test_hub.data["setting_ac_charge_t1_start_hour"] = 1
    test_hub.data["setting_ac_charge_t1_start_minute"] = 0
    assert entity_t1_start.native_value == datetime.time(1, 0)

    # Writing 01:30 -> (30 << 8) | 1 = 7681
    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await entity_t1_start.async_set_value(datetime.time(1, 30))
        mock_write.assert_called_once_with(68, (30 << 8) | 1)
        assert test_hub.data["setting_ac_charge_t1_start_hour"] == 1
        assert test_hub.data["setting_ac_charge_t1_start_minute"] == 30

    # Test reading and writing T1 End time (reg 69): 14:50 -> (50 << 8) | 14 = 12814
    desc_t1_end = HOLDING_REGISTERS[69]
    entity_t1_end = EG4Time(test_hub, dev_info_t1, desc_t1_end, 69, True)
    entity_t1_end.hass = MagicMock()
    entity_t1_end.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    entity_t1_end.async_write_ha_state = MagicMock()

    test_hub.data["setting_ac_charge_t1_end_hour"] = 14
    test_hub.data["setting_ac_charge_t1_end_minute"] = 50
    assert entity_t1_end.native_value == datetime.time(14, 50)

    # 2. Verify Sporadic Charge (register 2330 / addr 233)
    desc_sporadic = HOLDING_REGISTERS[2330]
    assert isinstance(desc_sporadic, EG4ModbusSelectEntityDescription)
    assert desc_sporadic.key == "setting_ac_charge_sporadic_charge"
    assert desc_sporadic.name == "AC Charge Sporadic Charge"
    assert desc_sporadic.address == 233
    assert desc_sporadic.bit_mask == 0x0001
    assert desc_sporadic.options == ["Disabled", "Enabled"]
    assert desc_sporadic.entity_category is None
    assert desc_sporadic.entity_registry_enabled_default is True
    assert desc_sporadic.icon == "mdi:battery-charging-wireless"

    dev_info_sporadic = test_hub.get_device_info(desc_sporadic.key, desc_sporadic.entity_category)
    assert dev_info_sporadic["name"] == "Test Inverter Inverter Settings"

    entity_sporadic = EG4Select(test_hub, dev_info_sporadic, desc_sporadic, 233, True)
    entity_sporadic.hass = MagicMock()
    entity_sporadic.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    entity_sporadic.async_write_ha_state = MagicMock()

    # Reading state: 0 -> Disabled, 1 -> Enabled
    test_hub.data["setting_ac_charge_sporadic_charge"] = 0
    assert entity_sporadic.current_option == "Disabled"

    test_hub.data["setting_ac_charge_sporadic_charge"] = 1
    assert entity_sporadic.current_option == "Enabled"

    # Selecting option "Enabled" (index 1) calls write_masked_register
    with patch.object(test_hub, "write_masked_register", return_value=True) as mock_masked_write:
        await entity_sporadic.async_select_option("Enabled")
        mock_masked_write.assert_called_once_with(233, 1, 0x0001)
        assert test_hub.data["setting_ac_charge_sporadic_charge"] == 1


async def test_forced_discharge_and_export_pv_only_entities(test_hub):
    """Test Forced Discharge (regs 82-89) and Export PV Only (reg 179 bit 3) entity configurations and behaviors."""
    from custom_components.eg4_inverter_modbus.const import HOLDING_REGISTERS

    async def mock_executor(func, *args, **kwargs):
        return func(*args, **kwargs)

    # 1. Forced Discharge Export PV Only (Select, Reg 179 bit 3)
    desc_export_pv = HOLDING_REGISTERS[17903]
    assert desc_export_pv.name == "Forced Discharge Export PV Only"
    assert desc_export_pv.key == "setting_ufunctionen2_export_pv_only"
    assert desc_export_pv.bit_mask == 0x0008
    assert desc_export_pv.entity_category is None

    dev_info = test_hub.get_device_info(desc_export_pv.key, desc_export_pv.entity_category)
    export_entity = EG4Select(test_hub, dev_info, desc_export_pv, 179, True)
    export_entity.hass = MagicMock()
    export_entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    export_entity.async_write_ha_state = MagicMock()

    test_hub.data["setting_ufunctionen2_export_pv_only"] = 1
    assert export_entity.current_option == "Enabled"

    with patch.object(test_hub, "write_masked_register", return_value=True) as mock_masked_write:
        await export_entity.async_select_option("Disabled")
        mock_masked_write.assert_called_once_with(179, 0, 0x0008)
        assert test_hub.data["setting_ufunctionen2_export_pv_only"] == 0

    # 2. Forced Discharge Power (Number, Reg 82)
    desc_pwr = HOLDING_REGISTERS[82]
    assert desc_pwr.name == "Forced Discharge Power"
    assert desc_pwr.scale == 0.1
    pwr_entity = EG4Number(test_hub, dev_info, desc_pwr, 82, True)
    pwr_entity.hass = MagicMock()
    pwr_entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    pwr_entity.async_write_ha_state = MagicMock()

    test_hub.data["setting_forced_discharge_power"] = 8.0
    assert pwr_entity.native_value == 8.0

    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await pwr_entity.async_set_native_value(8.0)
        mock_write.assert_called_once_with(82, 80)
        assert test_hub.data["setting_forced_discharge_power"] == 8.0

    # 2.5 AC Forced Discharge (Select, Reg 21 bit 10)
    desc_forced_dischg = HOLDING_REGISTERS[2111]
    assert desc_forced_dischg.name == "AC Forced Discharge"
    assert desc_forced_dischg.entity_category is None

    # Standby Mode (Select, Reg 21 bit 9)
    assert HOLDING_REGISTERS[2110].name == "Standby Mode"
    assert HOLDING_REGISTERS[2110].entity_category is None

    # 3. Forced Discharge Stop SOC (Number, Reg 83)
    desc_soc = HOLDING_REGISTERS[83]
    assert desc_soc.name == "Forced Discharge Stop SOC"
    assert desc_soc.scale == 1.0
    soc_entity = EG4Number(test_hub, dev_info, desc_soc, 83, True)
    soc_entity.hass = MagicMock()
    soc_entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
    soc_entity.async_write_ha_state = MagicMock()

    test_hub.data["setting_forced_discharge_stop_soc"] = 81
    assert soc_entity.native_value == 81

    with patch.object(test_hub, "write_register", return_value=True) as mock_write:
        await soc_entity.async_set_native_value(81)
        mock_write.assert_called_once_with(83, 81)
        assert test_hub.data["setting_forced_discharge_stop_soc"] == 81

    # 4. Forced Discharge T1-T3 Start/End Times (Time, Regs 84-89)
    for reg, slot, default_time in [
        (84, "t1_start", datetime.time(15, 0)),
        (85, "t1_end", datetime.time(21, 0)),
        (86, "t2_start", datetime.time(22, 22)),
        (87, "t2_end", datetime.time(23, 23)),
        (88, "t3_start", datetime.time(23, 24)),
        (89, "t3_end", datetime.time(23, 25)),
    ]:
        desc_time = HOLDING_REGISTERS[reg]
        time_entity = EG4Time(test_hub, dev_info, desc_time, reg, True)
        time_entity.hass = MagicMock()
        time_entity.hass.async_add_executor_job = AsyncMock(side_effect=mock_executor)
        time_entity.async_write_ha_state = MagicMock()

        test_hub.data[f"setting_forced_discharge_{slot}_hour"] = default_time.hour
        test_hub.data[f"setting_forced_discharge_{slot}_minute"] = default_time.minute
        assert time_entity.native_value == default_time

        expected_reg_val = (default_time.minute << 8) | default_time.hour
        with patch.object(test_hub, "write_register", return_value=True) as mock_write:
            await time_entity.async_set_value(default_time)
            mock_write.assert_called_once_with(reg, expected_reg_val)


async def test_readonly_holding_sensors(test_hub):
    """Test read-only mirror sensors for writable holding registers."""
    from custom_components.eg4_inverter_modbus.sensor import EG4ReadOnlyHoldingSensor
    from custom_components.eg4_inverter_modbus.const import HOLDING_REGISTERS
    from homeassistant.const import UnitOfPower, PERCENTAGE

    # 1. Number register: Forced Discharge Power (reg 82)
    desc_pwr = HOLDING_REGISTERS[82]
    dev_info = test_hub.get_device_info(desc_pwr.key, desc_pwr.entity_category)
    sensor_pwr = EG4ReadOnlyHoldingSensor(test_hub, dev_info, desc_pwr, True)
    assert sensor_pwr.name == "Forced Discharge Power"
    assert sensor_pwr.native_unit_of_measurement == UnitOfPower.KILO_WATT
    test_hub.data["setting_forced_discharge_power"] = 8.0
    assert sensor_pwr.native_value == 8.0

    # 2. Select register: AC Forced Discharge (reg 21 bit 10)
    desc_dischg = HOLDING_REGISTERS[2111]
    sensor_dischg = EG4ReadOnlyHoldingSensor(test_hub, dev_info, desc_dischg, True)
    assert sensor_dischg.name == "AC Forced Discharge"
    test_hub.data["setting_func_en_forced_dischg"] = 0
    assert sensor_dischg.native_value == "Disabled"
    test_hub.data["setting_func_en_forced_dischg"] = 1
    assert sensor_dischg.native_value == "Enabled"

    # 3. Select register: Forced Discharge Export PV Only (reg 179 bit 3)
    desc_export = HOLDING_REGISTERS[17903]
    sensor_export = EG4ReadOnlyHoldingSensor(test_hub, dev_info, desc_export, True)
    assert sensor_export.name == "Forced Discharge Export PV Only"
    test_hub.data["setting_ufunctionen2_export_pv_only"] = 1
    assert sensor_export.native_value == "Enabled"

    # 4. Time register: Forced Discharge T1 Start Time (reg 84)
    desc_time = HOLDING_REGISTERS[84]
    sensor_time = EG4ReadOnlyHoldingSensor(test_hub, dev_info, desc_time, True)
    assert sensor_time.name == "Forced Discharge T1 Start Time"
    test_hub.data["setting_forced_discharge_t1_start_hour"] = 15
    test_hub.data["setting_forced_discharge_t1_start_minute"] = 0
    assert sensor_time.native_value == "15:00"

    # Verify that capability_attributes does not raise AttributeError for any holding register mirror sensor
    from custom_components.eg4_inverter_modbus.const import (
        EG4ModbusNumberEntityDescription,
        EG4ModbusSelectEntityDescription,
        EG4ModbusTimeEntityDescription,
    )
    for desc in HOLDING_REGISTERS.values():
        if isinstance(desc, (EG4ModbusNumberEntityDescription, EG4ModbusSelectEntityDescription, EG4ModbusTimeEntityDescription)):
            dev_i = test_hub.get_device_info(desc.key, desc.entity_category)
            s = EG4ReadOnlyHoldingSensor(test_hub, dev_i, desc, True)
            assert s.capability_attributes is not None or s.capability_attributes is None
            assert s.state_attributes is not None or s.state_attributes is None
            assert s.extra_state_attributes is not None or s.extra_state_attributes is None





