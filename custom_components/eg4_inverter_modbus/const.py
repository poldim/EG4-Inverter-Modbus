from dataclasses import dataclass, field
from typing import Optional, Union

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import (
    SensorStateClass,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.components.number import NumberEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.helpers.entity import EntityCategory

from homeassistant.const import (
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
    UnitOfTemperature,
    UnitOfTime,
)

DOMAIN = "eg4_inverter_modbus"
DEFAULT_NAME = "EG4"
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_PORT = 502
ATTR_MANUFACTURER = "EG4"

# Add constants for options flow
CONF_ENABLE_READ_SENSORS = "enable_read_sensors"
CONF_ENABLE_WRITE_SENSORS = "enable_write_sensors"

@dataclass
class EG4ModbusSensorEntityDescription(SensorEntityDescription):
    """A class that describes EG4 sensor entities."""
    entity_category: Optional[EntityCategory] = None
    suggested_display_precision: Optional[int] = None
    entity_registry_enabled_default: bool = True

@dataclass
class EG4ModbusBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes EG4 binary sensor entities."""
    entity_category: Optional[EntityCategory] = None
    entity_registry_enabled_default: bool = True


@dataclass
class EG4ModbusNumberEntityDescription(NumberEntityDescription):
    """A class that describes EG4 number entities."""
    entity_category: Optional[EntityCategory] = EntityCategory.CONFIG
    scale: float = 1.0
    entity_registry_enabled_default: bool = False


@dataclass
class EG4ModbusSelectEntityDescription(SelectEntityDescription):
    """A class that describes EG4 select entities."""
    entity_category: Optional[EntityCategory] = EntityCategory.CONFIG
    entity_registry_enabled_default: bool = False


# --- Input Registers (Function Code 0x04) ---
INPUT_REGISTERS: dict[int, EG4ModbusSensorEntityDescription] = {
    0: EG4ModbusSensorEntityDescription(key="inverter_state", name="Inverter State", icon="mdi:information-outline"),
    1: EG4ModbusSensorEntityDescription(key="voltage_pv1", name="Voltage PV1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    2: EG4ModbusSensorEntityDescription(key="voltage_pv2", name="Voltage PV2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    3: EG4ModbusSensorEntityDescription(key="voltage_pv3", name="Voltage PV3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    4: EG4ModbusSensorEntityDescription(key="voltage_battery", name="Voltage Battery", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    5: EG4ModbusSensorEntityDescription(key="battery_soc", name="Battery SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    6: EG4ModbusSensorEntityDescription(key="battery_soh", name="Battery SOH", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:heart-pulse", suggested_display_precision=1),
    7: EG4ModbusSensorEntityDescription(key="power_pv1", name="Power PV1", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:solar-power"),
    8: EG4ModbusSensorEntityDescription(key="power_pv2", name="Power PV2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:solar-power", suggested_display_precision=1, entity_registry_enabled_default=False),
    9: EG4ModbusSensorEntityDescription(key="power_pv3", name="Power PV3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:solar-power", suggested_display_precision=1, entity_registry_enabled_default=False),
    10: EG4ModbusSensorEntityDescription(key="power_battery_charge", name="Power Battery Charge", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    11: EG4ModbusSensorEntityDescription(key="power_battery_discharge", name="Power Battery Discharge", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    12: EG4ModbusSensorEntityDescription(key="voltage_grid_l1l2", name="Voltage Grid L1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    13: EG4ModbusSensorEntityDescription(key="voltage_grid_l2l3", name="Voltage Grid L2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    14: EG4ModbusSensorEntityDescription(key="voltage_grid_l3l1", name="Voltage Grid L3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    15: EG4ModbusSensorEntityDescription(key="frequency_grid", name="Frequency Grid", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2, entity_registry_enabled_default=False),
    16: EG4ModbusSensorEntityDescription(key="power_inverter_output", name="Power Inverter Output", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    17: EG4ModbusSensorEntityDescription(key="power_ac_charge", name="Power AC Charge", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    18: EG4ModbusSensorEntityDescription(key="current_inverter_rms", name="Current Inverter RMS", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    19: EG4ModbusSensorEntityDescription(key="power_factor_inverter", name="Power Factor Inverter", device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    20: EG4ModbusSensorEntityDescription(key="voltage_inverter_l1l2", name="Voltage Inverter L1-L2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    21: EG4ModbusSensorEntityDescription(key="voltage_inverter_l2l3", name="Voltage Inverter L2-L3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    22: EG4ModbusSensorEntityDescription(key="voltage_inverter_l3l1", name="Voltage Inverter L3-L1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    23: EG4ModbusSensorEntityDescription(key="frequency_inverter", name="Frequency Inverter", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2, entity_registry_enabled_default=False),
    24: EG4ModbusSensorEntityDescription(key="power_inverter", name="Power Inverter", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    25: EG4ModbusSensorEntityDescription(key="power_apparent_inverter", name="Power Apparent Inverter", native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    26: EG4ModbusSensorEntityDescription(key="power_grid_export", name="Power Grid Export", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:transmission-tower-export"),
    27: EG4ModbusSensorEntityDescription(key="power_grid_import", name="Power Grid Import", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:transmission-tower-import"),
    28: EG4ModbusSensorEntityDescription(key="energy_daily_pv1", name="Energy Daily PV1", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:solar-power"),
    29: EG4ModbusSensorEntityDescription(key="energy_daily_pv2", name="Energy Daily PV2", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-power"),
    30: EG4ModbusSensorEntityDescription(key="energy_daily_pv3", name="Energy Daily PV3", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-power"),
    31: EG4ModbusSensorEntityDescription(key="energy_daily_inverter_output", name="Energy Daily Inverter Output", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    32: EG4ModbusSensorEntityDescription(key="energy_daily_ac_charge", name="Energy Daily AC Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    33: EG4ModbusSensorEntityDescription(key="energy_daily_battery_charge", name="Energy Daily Battery Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    34: EG4ModbusSensorEntityDescription(key="energy_daily_battery_discharge", name="Energy Daily Battery Discharge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    35: EG4ModbusSensorEntityDescription(key="energy_daily_inverter", name="Energy Daily Inverter", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    36: EG4ModbusSensorEntityDescription(key="energy_daily_grid_export", name="Energy Daily Grid Export", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    37: EG4ModbusSensorEntityDescription(key="energy_daily_grid_import", name="Energy Daily Grid Import", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    38: EG4ModbusSensorEntityDescription(key="voltage_bus_1", name="Voltage Bus 1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    39: EG4ModbusSensorEntityDescription(key="voltage_bus_2", name="Voltage Bus 2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    40: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv1", name="Energy Cumulative PV1", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    42: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv2", name="Energy Cumulative PV2", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    44: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv3", name="Energy Cumulative PV3", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    46: EG4ModbusSensorEntityDescription(key="energy_cumulative_inverter_output", name="Energy Cumulative Inverter Output", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    48: EG4ModbusSensorEntityDescription(key="energy_cumulative_ac_charge", name="Energy Cumulative AC Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    50: EG4ModbusSensorEntityDescription(key="energy_cumulative_battery_charge", name="Energy Cumulative Battery Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    52: EG4ModbusSensorEntityDescription(key="energy_cumulative_battery_discharge", name="Energy Cumulative Battery Discharge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    54: EG4ModbusSensorEntityDescription(key="energy_cumulative_inverter", name="Energy Cumulative Inverter", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    56: EG4ModbusSensorEntityDescription(key="energy_cumulative_grid_export", name="Energy Cumulative Grid Export", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    58: EG4ModbusSensorEntityDescription(key="energy_cumulative_grid_import", name="Energy Cumulative Grid Import", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    60: EG4ModbusSensorEntityDescription(key="fault_code", name="Fault Code", icon="mdi:alert-octagon", entity_category=EntityCategory.DIAGNOSTIC),
    62: EG4ModbusSensorEntityDescription(key="warning_code", name="Warning Code", icon="mdi:alert-outline", entity_category=EntityCategory.DIAGNOSTIC),
    64: EG4ModbusSensorEntityDescription(key="temperature_internal", name="Temperature Internal", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    65: EG4ModbusSensorEntityDescription(key="temperature_heatsink_dc", name="Heatsink Temperature DC", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    66: EG4ModbusSensorEntityDescription(key="temperature_heatsink_ac", name="Heatsink Temperature AC", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    67: EG4ModbusSensorEntityDescription(key="temperature_battery", name="Temperature Battery", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    69: EG4ModbusSensorEntityDescription(key="inverter_on_time", name="Inverter ON time", icon="mdi:timer-outline", device_class=SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC),
    71: EG4ModbusSensorEntityDescription(key="auto_test_status", name="Auto Test Status", icon="mdi:play-box-outline", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    77: EG4ModbusSensorEntityDescription(key="ac_input_type", name="AC Input Type", icon="mdi:power-plug"),
    81: EG4ModbusSensorEntityDescription(key="bms_current_max_charge", name="BMS Current Max Charge", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0, entity_registry_enabled_default=False),
    82: EG4ModbusSensorEntityDescription(key="bms_current_max_discharge", name="BMS Current Max Discharge", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0, entity_registry_enabled_default=False),
    83: EG4ModbusSensorEntityDescription(key="bms_voltage_charge_ref", name="BMS Voltage Charge Reference", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=1, entity_registry_enabled_default=False),
    84: EG4ModbusSensorEntityDescription(key="bms_voltage_discharge_cutoff", name="BMS Voltage Discharge Cutoff", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=1, entity_registry_enabled_default=False),
    85: EG4ModbusSensorEntityDescription(key="bms_status_0", name="BMS Status 0", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    86: EG4ModbusSensorEntityDescription(key="bms_status_1", name="BMS Status 1", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    87: EG4ModbusSensorEntityDescription(key="bms_status_2", name="BMS Status 2", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    88: EG4ModbusSensorEntityDescription(key="bms_status_3", name="BMS Status 3", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    89: EG4ModbusSensorEntityDescription(key="bms_status_4", name="BMS Status 4", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    90: EG4ModbusSensorEntityDescription(key="bms_status_5", name="BMS Status 5", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    91: EG4ModbusSensorEntityDescription(key="bms_status_6", name="BMS Status 6", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    92: EG4ModbusSensorEntityDescription(key="bms_status_7", name="BMS Status 7", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    93: EG4ModbusSensorEntityDescription(key="bms_status_8", name="BMS Status 8", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    94: EG4ModbusSensorEntityDescription(key="bms_status_9", name="BMS Status 9", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    95: EG4ModbusSensorEntityDescription(key="bms_status_inv", name="BMS Status Inverter Summary", icon="mdi:battery-heart-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    96: EG4ModbusSensorEntityDescription(key="battery_parallel_num", name="Battery Parallel Number", icon="mdi:battery-plus-variant", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    97: EG4ModbusSensorEntityDescription(key="battery_capacity_ah", name="Battery Capacity", native_unit_of_measurement="Ah", icon="mdi:battery-charging", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    98: EG4ModbusSensorEntityDescription(key="bms_current_battery", name="BMS Current Battery", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    99: EG4ModbusSensorEntityDescription(key="bms_fault_code", name="Fault Code BMS", icon="mdi:alert-octagon", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    100: EG4ModbusSensorEntityDescription(key="bms_warning_code", name="Warning Code BMS", icon="mdi:alert-outline", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    101: EG4ModbusSensorEntityDescription(key="bms_voltage_max_cell", name="BMS Voltage Max Cell", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    102: EG4ModbusSensorEntityDescription(key="bms_voltage_min_cell", name="BMS Voltage Min Cell", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    103: EG4ModbusSensorEntityDescription(key="bms_temperature_max_cell", name="BMS Temperature Max Cell", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    104: EG4ModbusSensorEntityDescription(key="bms_temperature_min_cell", name="BMS Temperature Min Cell", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    105: EG4ModbusSensorEntityDescription(key="bms_fw_update_state", name="BMS FW Update State", icon="mdi:update", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    106: EG4ModbusSensorEntityDescription(key="bms_cycle_count", name="Battery Cycle Count", icon="mdi:recycle", state_class=SensorStateClass.TOTAL_INCREASING),
    107: EG4ModbusSensorEntityDescription(key="voltage_battery_sample_inverter", name="Voltage Battery Sample Inverter", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    108: EG4ModbusSensorEntityDescription(key="temperature_t1", name="Temperature T1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    109: EG4ModbusSensorEntityDescription(key="temperature_t2", name="Temperature T2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    110: EG4ModbusSensorEntityDescription(key="temperature_t3", name="Temperature T3", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    111: EG4ModbusSensorEntityDescription(key="temperature_t4", name="Temperature T4", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    112: EG4ModbusSensorEntityDescription(key="temperature_t5", name="Temperature T5", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    120: EG4ModbusSensorEntityDescription(key="voltage_bus_p", name="Voltage Bus P", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    121: EG4ModbusSensorEntityDescription(key="voltage_generator", name="Voltage Generator", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    122: EG4ModbusSensorEntityDescription(key="frequency_generator", name="Frequency Generator", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2, entity_registry_enabled_default=False),
    123: EG4ModbusSensorEntityDescription(key="power_generator", name="Power Generator", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_registry_enabled_default=False),
    124: EG4ModbusSensorEntityDescription(key="energy_daily_generator", name="Energy Daily Generator", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    125: EG4ModbusSensorEntityDescription(key="energy_cumulative_generator", name="Energy Cumulative Generator", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    127: EG4ModbusSensorEntityDescription(key="voltage_inverter_l1n", name="Voltage Inverter L1-N", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    128: EG4ModbusSensorEntityDescription(key="voltage_inverter_l2n", name="Voltage Inverter L2-N", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    129: EG4ModbusSensorEntityDescription(key="power_inverter_l1n", name="Power Inverter L1-N", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_registry_enabled_default=False),
    130: EG4ModbusSensorEntityDescription(key="power_inverter_l2n", name="Power Inverter L2-N", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_registry_enabled_default=False),
    131: EG4ModbusSensorEntityDescription(key="power_apparent_inverter_l1n", name="Power Apparent Inverter L1-N", native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_registry_enabled_default=False),
    132: EG4ModbusSensorEntityDescription(key="power_apparent_inverter_l2n", name="Power Apparent Inverter L2-N", native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_registry_enabled_default=False),
    133: EG4ModbusSensorEntityDescription(key="energy_daily_inverter_l1n", name="Energy Daily Inverter L1-N", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    134: EG4ModbusSensorEntityDescription(key="energy_daily_inverter_l2n", name="Energy Daily Inverter L2-N", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    135: EG4ModbusSensorEntityDescription(key="energy_cumulative_inverter_l1n", name="Energy Cumulative Inverter L1-N", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    137: EG4ModbusSensorEntityDescription(key="energy_cumulative_inverter_l2n", name="Energy Cumulative Inverter L2-N", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    140: EG4ModbusSensorEntityDescription(key="current_afci_ch1", name="Current AFCI CH1", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    141: EG4ModbusSensorEntityDescription(key="current_afci_ch2", name="Current AFCI CH2", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    142: EG4ModbusSensorEntityDescription(key="current_afci_ch3", name="Current AFCI CH3", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    143: EG4ModbusSensorEntityDescription(key="current_afci_ch4", name="Current AFCI CH4", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    145: EG4ModbusSensorEntityDescription(key="afci_arc_ch1", name="AFCI Arc CH1", icon="mdi:flash-alert", entity_registry_enabled_default=False),
    146: EG4ModbusSensorEntityDescription(key="afci_arc_ch2", name="AFCI Arc CH2", icon="mdi:flash-alert", entity_registry_enabled_default=False),
    147: EG4ModbusSensorEntityDescription(key="afci_arc_ch3", name="AFCI Arc CH3", icon="mdi:flash-alert", entity_registry_enabled_default=False),
    148: EG4ModbusSensorEntityDescription(key="afci_arc_ch4", name="AFCI Arc CH4", icon="mdi:flash-alert", entity_registry_enabled_default=False),
    149: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch1", name="AFCI Max Arc CH1", icon="mdi:flash", entity_registry_enabled_default=False),
    150: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch2", name="AFCI Max Arc CH2", icon="mdi:flash", entity_registry_enabled_default=False),
    151: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch3", name="AFCI Max Arc CH3", icon="mdi:flash", entity_registry_enabled_default=False),
    152: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch4", name="AFCI Max Arc CH4", icon="mdi:flash", entity_registry_enabled_default=False),
    # --- Calculated Sensors ---
    -1: EG4ModbusSensorEntityDescription(key="power_pv_total", name="Power PV Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:solar-power"),
    -2: EG4ModbusSensorEntityDescription(key="power_battery_total", name="Power Battery Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:home-battery-outline"),
    -3: EG4ModbusSensorEntityDescription(key="energy_daily_pv_total", name="Energy Daily PV Total", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, icon="mdi:solar-power", suggested_display_precision=1),
    -4: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv", name="Energy Cumulative PV", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, icon="mdi:solar-power", suggested_display_precision=1),
    -5: EG4ModbusBinarySensorEntityDescription(key="inverter_time_accurate", name="Inverter Time Accurate", device_class=BinarySensorDeviceClass.CONNECTIVITY, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),  ### DOES NOT WORK
    -6: EG4ModbusSensorEntityDescription(key="parallel_master_slave", name="Parallel Master/Slave", icon="mdi:vector-combine", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -7: EG4ModbusSensorEntityDescription(key="parallel_phase", name="Parallel Phase", icon="mdi:vector-combine", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -8: EG4ModbusSensorEntityDescription(key="parallel_number", name="Parallel Number", icon="mdi:vector-combine", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -9: EG4ModbusSensorEntityDescription(key="power_grid_total", name="Power Grid Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:transmission-tower"),
    -10: EG4ModbusSensorEntityDescription(key="voltage_pv_average", name="Voltage PV Average", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:solar-power"),
    -11: EG4ModbusSensorEntityDescription(key="inverter_uptime_minutes", name="Inverter Uptime (minutes)", native_unit_of_measurement=UnitOfTime.MINUTES, state_class=SensorStateClass.MEASUREMENT, icon="mdi:timer-plus-outline", entity_registry_enabled_default=False),
    -12: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch1", name="AFCI Alarm CH1", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -13: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch2", name="AFCI Alarm CH2", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -14: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch3", name="AFCI Alarm CH3", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -15: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch4", name="AFCI Alarm CH4", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -16: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch1", name="AFCI Self-Test CH1", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:alert"),
    -17: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch2", name="AFCI Self-Test CH2", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:alert"),
    -18: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch3", name="AFCI Self-Test CH3", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:alert"),
    -19: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch4", name="AFCI Self-Test CH4", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:alert"),
}

# --- Holding Registers (Function Codes 0x03, 0x06, 0x10) ---
# A single dictionary for all holding registers. The setup process will determine
# whether to create a sensor, number, or select entity based on the description type.
HOLDING_REGISTERS: dict[int, Union[EG4ModbusSensorEntityDescription, EG4ModbusNumberEntityDescription, EG4ModbusSelectEntityDescription]] = {
    9: EG4ModbusSensorEntityDescription(key="info_com_version", name="Info COM Version", icon="mdi:information-outline", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    10: EG4ModbusSensorEntityDescription(key="info_controller_version", name="Info Control Version", icon="mdi:information-outline", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    22: EG4ModbusNumberEntityDescription(key="setting_voltage_pv_start", name="PV Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=90, native_max_value=500),
    23: EG4ModbusNumberEntityDescription(key="setting_time_grid_connection_wait", name="Grid Connection Wait Time", native_unit_of_measurement=UnitOfTime.SECONDS, icon="mdi:cogs", native_min_value=30, native_max_value=600),
    24: EG4ModbusNumberEntityDescription(key="setting_time_reconnection_wait", name="Reconnection Wait Time", native_unit_of_measurement=UnitOfTime.SECONDS, icon="mdi:cogs", native_min_value=0, native_max_value=900),
    64: EG4ModbusNumberEntityDescription(key="setting_percent_charge_power", name="Charge Power Percentage", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    65: EG4ModbusNumberEntityDescription(key="setting_percent_discharge_power", name="Discharge Power Percentage", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    66: EG4ModbusNumberEntityDescription(key="setting_percent_ac_charge_power", name="AC Charge Percentage", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    67: EG4ModbusNumberEntityDescription(key="setting_limit_soc_ac_charge", name="AC Charging SOC Limit", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    99: EG4ModbusNumberEntityDescription(key="setting_voltage_charge_ref", name="Charge Voltage Reference", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=50, native_max_value=59),
    100: EG4ModbusNumberEntityDescription(key="setting_voltage_discharge_cutoff", name="Discharge Cutoff Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=40, native_max_value=50),
    101: EG4ModbusNumberEntityDescription(key="setting_current_charge", name="Charge Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, icon="mdi:cogs", native_min_value=0, native_max_value=140),
    102: EG4ModbusNumberEntityDescription(key="setting_current_discharge", name="Discharge Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, icon="mdi:cogs", native_min_value=0, native_max_value=140),
    103: EG4ModbusNumberEntityDescription(key="setting_max_backflow_power", name="Max Backflow Power", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    105: EG4ModbusNumberEntityDescription(key="setting_eod_soc", name="EOD SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=10, native_max_value=90),
    116: EG4ModbusNumberEntityDescription(key="setting_ptouser_start_discharge", name="Ptouser Start Discharge", native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:cogs", native_min_value=50, native_max_value=10000),
    118: EG4ModbusNumberEntityDescription(key="setting_voltage_start_derating", name="Voltage Start Derating", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1),
    119: EG4ModbusNumberEntityDescription(key="setting_power_offset_wct", name="Power Offset WCT", native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:cogs", native_min_value=-1000, native_max_value=1000),
    125: EG4ModbusNumberEntityDescription(key="setting_soc_low_limit_inverter_discharge", name="SOC Low Limit Inverter Discharge", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    144: EG4ModbusNumberEntityDescription(key="setting_voltage_float_charge", name="Float Charge Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=50, native_max_value=56),
    147: EG4ModbusNumberEntityDescription(key="setting_battery_capacity", name="Battery Capacity", native_unit_of_measurement="Ah", icon="mdi:cogs", native_min_value=0, native_max_value=10000),
    148: EG4ModbusNumberEntityDescription(key="setting_battery_nominal_voltage", name="Battery Nominal Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=40, native_max_value=59),
    149: EG4ModbusNumberEntityDescription(key="setting_voltage_equalization", name="Equalization Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=50, native_max_value=59),
    150: EG4ModbusNumberEntityDescription(key="setting_equalization_interval", name="Equalization Interval", native_unit_of_measurement=UnitOfTime.DAYS, icon="mdi:cogs", native_min_value=0, native_max_value=365),
    151: EG4ModbusNumberEntityDescription(key="setting_equalization_time", name="Equalization Time", native_unit_of_measurement=UnitOfTime.HOURS, icon="mdi:cogs", native_min_value=0, native_max_value=24),
    158: EG4ModbusNumberEntityDescription(key="setting_voltage_ac_charge_start", name="AC Charge Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=38.4, native_max_value=52),
    159: EG4ModbusNumberEntityDescription(key="setting_voltage_ac_charge_end", name="AC Charge End Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=48, native_max_value=59),
    160: EG4ModbusNumberEntityDescription(key="setting_soc_ac_charge_start", name="AC Charge Start SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=90),
    161: EG4ModbusNumberEntityDescription(key="setting_soc_ac_charge_end", name="AC Charge End SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=20, native_max_value=100),
    162: EG4ModbusNumberEntityDescription(key="setting_voltage_battery_low", name="Battery Low Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=40, native_max_value=50),
    163: EG4ModbusNumberEntityDescription(key="setting_voltage_battery_low_back", name="Battery Low Back Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=42, native_max_value=52),
    164: EG4ModbusNumberEntityDescription(key="setting_soc_battery_low", name="Battery Low SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=90),
    165: EG4ModbusNumberEntityDescription(key="setting_soc_battery_low_back", name="Battery Low Back SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=20, native_max_value=100),
    166: EG4ModbusNumberEntityDescription(key="setting_voltage_battery_low_to_utility", name="Battery Low to Utility Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=44.4, native_max_value=51.4),
    167: EG4ModbusNumberEntityDescription(key="setting_soc_battery_low_to_utility", name="Battery Low to Utility SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=100),
    168: EG4ModbusNumberEntityDescription(key="setting_current_ac_charge_battery", name="AC Charge Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, icon="mdi:cogs", native_min_value=0, native_max_value=140),
    169: EG4ModbusNumberEntityDescription(key="setting_voltage_ongrid_eod", name="Ongrid EOD Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=40, native_max_value=56),
    176: EG4ModbusNumberEntityDescription(key="setting_power_max_grid_input", name="Max Grid Input Power", native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:cogs"),
    177: EG4ModbusNumberEntityDescription(key="setting_power_gen_rated", name="Gen Rated Power", native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:cogs"),
    194: EG4ModbusNumberEntityDescription(key="setting_voltage_gen_charge_start", name="Gen Charge Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=38.4, native_max_value=52),
    195: EG4ModbusNumberEntityDescription(key="setting_voltage_gen_charge_end", name="Gen Charge End Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, icon="mdi:cogs", scale=0.1, native_min_value=48, native_max_value=59),
    196: EG4ModbusNumberEntityDescription(key="setting_soc_gen_charge_start", name="Gen Charge Start SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=0, native_max_value=90),
    197: EG4ModbusNumberEntityDescription(key="setting_soc_gen_charge_end", name="Gen Charge End SOC", native_unit_of_measurement=PERCENTAGE, icon="mdi:cogs", native_min_value=20, native_max_value=100),
    198: EG4ModbusNumberEntityDescription(key="setting_current_max_gen_charge_battery", name="Max Gen Charge Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, icon="mdi:cogs", native_min_value=0, native_max_value=60),
    16: EG4ModbusSelectEntityDescription(key="setting_language", name="Language", icon="mdi:cogs", options=["English", "German"]),
    20: EG4ModbusSelectEntityDescription(key="setting_pv_input_model", name="PV Input Model", icon="mdi:cogs", options=["No PV", "PV1 in", "PV2 in", "PV3 in", "PV1&2 in", "PV1&3 in", "PV2&3 in", "PV1&2&3 in"]),
    90: EG4ModbusSelectEntityDescription(key="setting_voltage_inverter", name="Inverter Voltage", icon="mdi:cogs", options=["230", "240", "277", "208"]),
    91: EG4ModbusSelectEntityDescription(key="setting_frequency_inverter", name="Inverter Frequency", icon="mdi:cogs", options=["50", "60"]),
    112: EG4ModbusSelectEntityDescription(key="setting_system_type", name="System Type", icon="mdi:cogs", options=["No Parallel", "Single Phase Parallel (Master)", "Slave", "Three Phase Parallel (Master)"]),
    145: EG4ModbusSelectEntityDescription(key="setting_output_priority_config", name="Output Priority Config", icon="mdi:cogs", options=["Battery First", "PV First", "AC First"]),
    146: EG4ModbusSelectEntityDescription(key="setting_line_mode", name="Line Mode", icon="mdi:cogs", options=["APL", "UPS", "GEN"]),
}


# --- Enums and Flags ---
INVERTER_STATUS_CODES = {
    0x00: "Standby", 0x01: "Fault", 0x02: "Programming", 0x04: "PV on-grid mode",
    0x08: "PV Charge mode", 0x0C: "PV Charge+on-grid mode", 0x10: "Battery on-grid mode",
    0x14: "PV+ Battery on-grid mode", 0x20: "AC Charge mode", 0x28: "PV+AC charge mode",
    0x40: "Battery off-grid mode", 0x80: "PV off-grid mode", 0x88: "PV charge +off-grid mode",
    0xC0: "PV+battery off-grid mode",
}

AC_INPUT_TYPE_CODES = {
    0: "Grid",
    1: "Generator",
}

FAULT_CODES = {
    (1 << 0): "Internal communication fault 1", (1 << 1): "Model fault", (1 << 8): "Paralleling CAN communication lost",
    (1 << 9): "Master unit lost in paralleling system", (1 << 10): "Multiple master units in paralleling system",
    (1 << 11): "AC input inconsistent in paralleling system", (1 << 12): "UPS short", (1 << 13): "Reverse current on UPS output",
    (1 << 14): "BUS short", (1 << 15): "Grid phases inconsistent in 3phase paralleling system", (1 << 16): "Relay Check Fault",
    (1 << 17): "Internal communication fault 2", (1 << 18): "Internal communication fault 3", (1 << 19): "BUS Voltage high",
    (1 << 20): "EPS connection fault", (1 << 21): "PV Voltage high", (1 << 22): "Over current protection",
    (1 << 23): "Neutral fault", (1 << 24): "PV short", (1 << 25): "Radiator temperature out of range",
    (1 << 26): "Internal Fault", (1 << 27): "Sample inconsistent between Main CPU and redundant CPU", (1 << 31): "Internal communication fault 4",
}

WARNING_CODES = {
    (1 << 0): "Battery communication failure", (1 << 1): "AFCI communication failure", (1 << 2): "AFCI High",
    (1 << 3): "Meter communication failure", (1 << 4): "Both charge and discharge forbidden by battery",
    (1 << 5): "Auto test failed", (1 << 7): "LCD communication failure", (1 << 8): "FW version mismatching",
    (1 << 9): "Fan stuck", (1 << 11): "Parallel number out of range", (1 << 15): "Battery reverse connection",
    (1 << 16): "Grid power outage", (1 << 17): "Grid voltage out of range", (1 << 18): "Grid frequency out of range",
    (1 << 20): "PV insulation low", (1 << 21): "Leakage current high", (1 << 22): "DCI high",
    (1 << 23): "PV short", (1 << 25): "Battery voltage high", (1 << 26): "Battery voltage low",
    (1 << 27): "Battery open circuit", (1 << 28): "EPS overload", (1 << 29): "EPS voltage high",
    (1 << 30): "Meter reverse connection", (1 << 31): "DCV high",
}