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
from homeassistant.components.time import TimeEntityDescription
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
MAX_BATTERIES = 6

DOMAIN = "eg4_inverter_modbus"
DEFAULT_NAME = "EG4"
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_PORT = 502
ATTR_MANUFACTURER = "EG4"

# Add constants for options flow
CONF_ENABLE_ALL_READ_SENSORS = "enable_all_read_sensors"
CONF_ENABLE_WRITE_SENSORS = "enable_write_sensors"

@dataclass(frozen=True, kw_only=True)
class EG4ModbusSensorEntityDescription(SensorEntityDescription):
    """A class that describes EG4 sensor entities."""
    entity_category: Optional[EntityCategory] = None
    suggested_display_precision: Optional[int] = None
    entity_registry_enabled_default: bool = True
    address: Optional[int] = None
    bit_mask: Optional[int] = None
    scale: Optional[float] = None

@dataclass(frozen=True, kw_only=True)
class EG4ModbusBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes EG4 binary sensor entities."""
    entity_category: Optional[EntityCategory] = None
    entity_registry_enabled_default: bool = True


@dataclass(frozen=True, kw_only=True)
class EG4ModbusNumberEntityDescription(NumberEntityDescription):
    """A class that describes EG4 number entities."""
    entity_category: Optional[EntityCategory] = EntityCategory.CONFIG
    scale: float = 1.0
    entity_registry_enabled_default: bool = False
    address: Optional[int] = None
    bit_mask: Optional[int] = None


@dataclass(frozen=True, kw_only=True)
class EG4ModbusSelectEntityDescription(SelectEntityDescription):
    """A class that describes EG4 select entities."""
    entity_category: Optional[EntityCategory] = EntityCategory.CONFIG
    entity_registry_enabled_default: bool = False
    address: Optional[int] = None
    bit_mask: Optional[int] = None
    option_dict: Optional[dict[int, str]] = None


@dataclass(frozen=True, kw_only=True)
class EG4ModbusTimeEntityDescription(TimeEntityDescription):
    """Describes EG4 Modbus time entity."""
    entity_category: Optional[EntityCategory] = EntityCategory.CONFIG
    address: Optional[int] = None


# --- Input Registers (Function Code 0x04), ---
BATTERY_SENSOR_DEFINITIONS = {
    "capacity_pack": EG4ModbusSensorEntityDescription(key="{}_capacity_pack", name="Battery {} Capacity", native_unit_of_measurement="Ah", device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "capacity_system": EG4ModbusSensorEntityDescription(key="{}_capacity_system", name="Battery {} Capacity of System", native_unit_of_measurement="Ah", device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    "current_max_charge": EG4ModbusSensorEntityDescription(key="{}_current_max_charge", name="Battery {} Current Charge Max", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "current_max_discharge": EG4ModbusSensorEntityDescription(key="{}_current_max_discharge", name="Battery {} Current Discharge Max", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "voltage": EG4ModbusSensorEntityDescription(key="{}_voltage", name="Battery {} Pack Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    "current": EG4ModbusSensorEntityDescription(key="{}_current", name="Battery {} Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    "soh": EG4ModbusSensorEntityDescription(key="{}_soh", name="Battery {} SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    "soc": EG4ModbusSensorEntityDescription(key="{}_soc", name="Battery {} SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    "cycle_count": EG4ModbusSensorEntityDescription(key="{}_cycle_count", name="Battery {} Cycle Count", state_class=SensorStateClass.TOTAL_INCREASING),
    "max_cell_temp": EG4ModbusSensorEntityDescription(key="{}_max_cell_temp", name="Battery {} Cell Temperature Max", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "min_cell_temp": EG4ModbusSensorEntityDescription(key="{}_min_cell_temp", name="Battery {} Cell Temperature Min", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "max_cell_voltage": EG4ModbusSensorEntityDescription(key="{}_max_cell_voltage", name="Battery {} Cell Voltage Max", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    "min_cell_voltage": EG4ModbusSensorEntityDescription(key="{}_min_cell_voltage", name="Battery {} Cell Voltage Min", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    "cell_temp_min": EG4ModbusSensorEntityDescription(key="{}_cell_temp_min", name="Battery {} Cell with Min Temperature"),
    "cell_temp_max": EG4ModbusSensorEntityDescription(key="{}_cell_temp_max", name="Battery {} Cell with Max Temperature"),
    "cell_voltage_min": EG4ModbusSensorEntityDescription(key="{}_cell_voltage_min", name="Battery {} Cell with Min Voltage"),
    "cell_voltage_max": EG4ModbusSensorEntityDescription(key="{}_cell_voltage_max", name="Battery {} Cell with Max Voltage"),
    "firmware": EG4ModbusSensorEntityDescription(key="{}_firmware", name="Battery {} Firmware Version"),
    "remaining_capacity": EG4ModbusSensorEntityDescription(key="{}_remaining_capacity", name="Battery {} Remaining Capacity", native_unit_of_measurement="Ah", device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "cell_voltage_delta": EG4ModbusSensorEntityDescription(key="{}_cell_voltage_delta", name="Battery {} Cell Voltage Delta", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    "cell_temp_delta": EG4ModbusSensorEntityDescription(key="{}_cell_temp_delta", name="Battery {} Cell Temperature Delta", native_unit_of_measurement=None, device_class=None, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    "real_power": EG4ModbusSensorEntityDescription(key="{}_real_power", name="Battery {} Real Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0),
    "current_flow_rate": EG4ModbusSensorEntityDescription(key="{}_current_flow_rate", name="Battery {} Current Flow Rate", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    "serial_id": EG4ModbusSensorEntityDescription(key="{}_serial_id", name="Battery {} Serial ID"),
}

INPUT_REGISTERS: dict[int, EG4ModbusSensorEntityDescription] = {
    0: EG4ModbusSensorEntityDescription(key="inverter_mode", name="Inverter Mode"),
    1: EG4ModbusSensorEntityDescription(key="voltage_pv1", name="Voltage PV1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, icon="mdi:solar-panel-large"),
    2: EG4ModbusSensorEntityDescription(key="voltage_pv2", name="Voltage PV2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-panel-large"),
    3: EG4ModbusSensorEntityDescription(key="voltage_pv3", name="Voltage PV3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-panel-large"),
    4: EG4ModbusSensorEntityDescription(key="voltage_battery", name="Battery Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    5: EG4ModbusSensorEntityDescription(key="battery_soc", name="Battery SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    6: EG4ModbusSensorEntityDescription(key="battery_soh", name="Battery SOH", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, icon="mdi:heart-pulse"),
    7: EG4ModbusSensorEntityDescription(key="power_pv1", name="Power PV1", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, icon="mdi:solar-power"),
    8: EG4ModbusSensorEntityDescription(key="power_pv2", name="Power PV2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, icon="mdi:solar-power"),
    9: EG4ModbusSensorEntityDescription(key="power_pv3", name="Power PV3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, icon="mdi:solar-power"),
    10: EG4ModbusSensorEntityDescription(key="power_battery_charge", name="Power Battery Charge", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    11: EG4ModbusSensorEntityDescription(key="power_battery_discharge", name="Power Battery Discharge", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    12: EG4ModbusSensorEntityDescription(key="voltage_grid_l1l2", name="Voltage Grid L1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, icon="mdi:transmission-tower"),
    13: EG4ModbusSensorEntityDescription(key="voltage_grid_l2l3", name="Voltage Grid L2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    14: EG4ModbusSensorEntityDescription(key="voltage_grid_l3l1", name="Voltage Grid L3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    15: EG4ModbusSensorEntityDescription(key="frequency_grid", name="Frequency Grid", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    16: EG4ModbusSensorEntityDescription(key="power_inverter_output", name="Power Inverter Output", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:home-lightning-bolt"),
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
    31: EG4ModbusSensorEntityDescription(key="energy_daily_inverter_output", name="Energy Daily Inverter Output", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:home-lightning-bolt"),
    32: EG4ModbusSensorEntityDescription(key="energy_daily_ac_charge", name="Energy Daily AC Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    33: EG4ModbusSensorEntityDescription(key="energy_daily_battery_charge", name="Energy Daily Battery Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    34: EG4ModbusSensorEntityDescription(key="energy_daily_battery_discharge", name="Energy Daily Battery Discharge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    35: EG4ModbusSensorEntityDescription(key="energy_daily_inverter", name="Energy Daily Inverter", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1),
    36: EG4ModbusSensorEntityDescription(key="energy_daily_grid_export", name="Energy Daily Grid Export", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:transmission-tower-export"),
    37: EG4ModbusSensorEntityDescription(key="energy_daily_grid_import", name="Energy Daily Grid Import", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:transmission-tower-import"),
    38: EG4ModbusSensorEntityDescription(key="voltage_bus_1", name="Voltage Bus 1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    39: EG4ModbusSensorEntityDescription(key="voltage_bus_2", name="Voltage Bus 2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    40: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv1", name="Energy Cumulative PV1", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-power"),
    42: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv2", name="Energy Cumulative PV2", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-power"),
    44: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv3", name="Energy Cumulative PV3", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:solar-power"),
    46: EG4ModbusSensorEntityDescription(key="energy_cumulative_inverter_output", name="Energy Cumulative Inverter Output", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:home-lightning-bolt"),
    48: EG4ModbusSensorEntityDescription(key="energy_cumulative_ac_charge", name="Energy Cumulative AC Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    50: EG4ModbusSensorEntityDescription(key="energy_cumulative_battery_charge", name="Energy Cumulative Battery Charge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    52: EG4ModbusSensorEntityDescription(key="energy_cumulative_battery_discharge", name="Energy Cumulative Battery Discharge", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    54: EG4ModbusSensorEntityDescription(key="energy_cumulative_inverter", name="Energy Cumulative Inverter", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False),
    56: EG4ModbusSensorEntityDescription(key="energy_cumulative_grid_export", name="Energy Cumulative Grid Export", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:transmission-tower-export"),
    58: EG4ModbusSensorEntityDescription(key="energy_cumulative_grid_import", name="Energy Cumulative Grid Import", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:transmission-tower-import"),
    60: EG4ModbusSensorEntityDescription(key="fault_code", name="Fault Code", entity_category=EntityCategory.DIAGNOSTIC),
    62: EG4ModbusSensorEntityDescription(key="warning_code", name="Warning Code", entity_category=EntityCategory.DIAGNOSTIC),
    64: EG4ModbusSensorEntityDescription(key="temperature_internal", name="Temperature Internal", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    65: EG4ModbusSensorEntityDescription(key="temperature_heatsink_dc", name="Heatsink Temperature DC", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    66: EG4ModbusSensorEntityDescription(key="temperature_heatsink_ac", name="Heatsink Temperature AC", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    67: EG4ModbusSensorEntityDescription(key="temperature_battery", name="Temperature Battery", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    69: EG4ModbusSensorEntityDescription(key="inverter_on_time", name="Inverter ON time", device_class=SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC),
    71: EG4ModbusSensorEntityDescription(key="auto_test_status", name="Auto Test Status", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    77: EG4ModbusSensorEntityDescription(key="ac_input_type", name="AC Input Type"),
    81: EG4ModbusSensorEntityDescription(key="bms_current_max_charge", name="BMS Current Max Charge", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0, entity_registry_enabled_default=False, scale=10.0),
    82: EG4ModbusSensorEntityDescription(key="bms_current_max_discharge", name="BMS Current Max Discharge", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0, entity_registry_enabled_default=False, scale=10.0),
    83: EG4ModbusSensorEntityDescription(key="bms_voltage_charge_ref", name="BMS Voltage Charge Reference", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=1, entity_registry_enabled_default=False),
    84: EG4ModbusSensorEntityDescription(key="bms_voltage_discharge_cutoff", name="BMS Voltage Discharge Cutoff", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=1, entity_registry_enabled_default=False),
    85: EG4ModbusSensorEntityDescription(key="bms_status_0", name="BMS Status 0", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    86: EG4ModbusSensorEntityDescription(key="bms_status_1", name="BMS Status 1", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    87: EG4ModbusSensorEntityDescription(key="bms_status_2", name="BMS Status 2", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    88: EG4ModbusSensorEntityDescription(key="bms_status_3", name="BMS Status 3", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    89: EG4ModbusSensorEntityDescription(key="bms_status_4", name="BMS Status 4", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    90: EG4ModbusSensorEntityDescription(key="bms_status_5", name="BMS Status 5", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    91: EG4ModbusSensorEntityDescription(key="bms_status_6", name="BMS Status 6", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    92: EG4ModbusSensorEntityDescription(key="bms_status_7", name="BMS Status 7", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    93: EG4ModbusSensorEntityDescription(key="bms_status_8", name="BMS Status 8", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    94: EG4ModbusSensorEntityDescription(key="bms_status_9", name="BMS Status 9", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    95: EG4ModbusSensorEntityDescription(key="bms_status_inv", name="BMS Status Inverter Summary", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, icon="mdi:battery-heart-variant"),
    96: EG4ModbusSensorEntityDescription(key="battery_parallel_num", name="Battery Parallel Number", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    97: EG4ModbusSensorEntityDescription(key="battery_capacity_ah", name="Battery Capacity", native_unit_of_measurement="Ah", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    98: EG4ModbusSensorEntityDescription(key="bms_current_battery", name="Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    99: EG4ModbusSensorEntityDescription(key="bms_fault_code", name="Fault Code BMS", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    100: EG4ModbusSensorEntityDescription(key="bms_warning_code", name="Warning Code BMS", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    101: EG4ModbusSensorEntityDescription(key="bms_voltage_max_cell", name="BMS Voltage Max Cell", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    102: EG4ModbusSensorEntityDescription(key="bms_voltage_min_cell", name="BMS Voltage Min Cell", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    103: EG4ModbusSensorEntityDescription(key="bms_temperature_max_cell", name="BMS Temperature Max Cell", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    104: EG4ModbusSensorEntityDescription(key="bms_temperature_min_cell", name="BMS Temperature Min Cell", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    105: EG4ModbusSensorEntityDescription(key="bms_fw_update_state", name="BMS FW Update State", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    106: EG4ModbusSensorEntityDescription(key="bms_cycle_count", name="Battery Cycle Count", state_class=SensorStateClass.TOTAL_INCREASING),
    107: EG4ModbusSensorEntityDescription(key="voltage_battery_sample_inverter", name="Voltage Battery Sample Inverter", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    108: EG4ModbusSensorEntityDescription(key="temperature_t1", name="Temperature T1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    109: EG4ModbusSensorEntityDescription(key="temperature_t2", name="Temperature T2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, entity_registry_visible_default=False),
    110: EG4ModbusSensorEntityDescription(key="temperature_t3", name="Temperature T3", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, entity_registry_visible_default=False),
    111: EG4ModbusSensorEntityDescription(key="temperature_t4", name="Temperature T4", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, entity_registry_visible_default=False),
    112: EG4ModbusSensorEntityDescription(key="temperature_t5", name="Temperature T5", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, entity_registry_visible_default=False),
    114: EG4ModbusSensorEntityDescription(key="power_load_on_grid", name="Power Load On Grid", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, icon="mdi:transmission-tower"),
    120: EG4ModbusSensorEntityDescription(key="voltage_bus_p", name="Voltage Bus P", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    121: EG4ModbusSensorEntityDescription(key="voltage_generator", name="Voltage Generator", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
    122: EG4ModbusSensorEntityDescription(key="frequency_generator", name="Frequency Generator", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
    123: EG4ModbusSensorEntityDescription(key="power_generator", name="Power Generator", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
    124: EG4ModbusSensorEntityDescription(key="energy_daily_generator", name="Energy Daily Generator", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
    125: EG4ModbusSensorEntityDescription(key="energy_cumulative_generator", name="Energy Cumulative Generator", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
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
    140: EG4ModbusSensorEntityDescription(key="afci_current_ch1", name="AFCI Current CH1", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-flash"),
    141: EG4ModbusSensorEntityDescription(key="afci_current_ch2", name="AFCI Current CH2", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-flash"),
    142: EG4ModbusSensorEntityDescription(key="afci_current_ch3", name="AFCI Current CH3", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-flash"),
    143: EG4ModbusSensorEntityDescription(key="afci_current_ch4", name="AFCI Current CH4", native_unit_of_measurement="mA", device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-flash"),
    145: EG4ModbusSensorEntityDescription(key="afci_arc_ch1", name="AFCI Arc CH1", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    146: EG4ModbusSensorEntityDescription(key="afci_arc_ch2", name="AFCI Arc CH2", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    147: EG4ModbusSensorEntityDescription(key="afci_arc_ch3", name="AFCI Arc CH3", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    148: EG4ModbusSensorEntityDescription(key="afci_arc_ch4", name="AFCI Arc CH4", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    149: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch1", name="AFCI Max Arc CH1", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    150: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch2", name="AFCI Max Arc CH2", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    151: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch3", name="AFCI Max Arc CH3", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    152: EG4ModbusSensorEntityDescription(key="afci_max_arc_ch4", name="AFCI Max Arc CH4", entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:flash-alert"),
    153: EG4ModbusSensorEntityDescription(key="power_inverter_ac_coupled", name="Power Inverter AC Coupled", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0),
    170: EG4ModbusSensorEntityDescription(key="power_load", name="Power Load", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, icon="mdi:home-lightning-bolt"),
    171: EG4ModbusSensorEntityDescription(key="energy_daily_load", name="Energy Daily Load", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:home-lightning-bolt"),
    172: EG4ModbusSensorEntityDescription(key="energy_cumulative_load", name="Energy Cumulative Load", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:home-lightning-bolt"),
    180: EG4ModbusSensorEntityDescription(key="power_inverter_on_grid_l2", name="Power Inverter On Grid L2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    181: EG4ModbusSensorEntityDescription(key="power_inverter_on_grid_l3", name="Power Inverter On Grid L3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    182: EG4ModbusSensorEntityDescription(key="power_charging_rectification_l2", name="Power Charging Rectification L2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    183: EG4ModbusSensorEntityDescription(key="power_charging_rectification_l3", name="Power Charging Rectification L3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    184: EG4ModbusSensorEntityDescription(key="power_grid_output_load_terminal_l2", name="Power Output Grid Terminal L2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    185: EG4ModbusSensorEntityDescription(key="power_grid_output_load_terminal_l3", name="Power Output Grid Terminal L3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    186: EG4ModbusSensorEntityDescription(key="power_grid_power_supply_l2", name="Power Grid Supply L2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    187: EG4ModbusSensorEntityDescription(key="power_grid_power_supply_l3", name="Power Grid Supply L3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:transmission-tower"),
    188: EG4ModbusSensorEntityDescription(key="power_gen_terminal_l2", name="Power Gen Terminal L2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
    189: EG4ModbusSensorEntityDescription(key="power_gen_terminal_l3", name="Power Gen Terminal L3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False, icon="mdi:generator-portable"),
    190: EG4ModbusSensorEntityDescription(key="current_inverter_rms_l2", name="Current Inverter RMS L2", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    191: EG4ModbusSensorEntityDescription(key="current_inverter_rms_l3", name="Current Inverter RMS L3", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    192: EG4ModbusSensorEntityDescription(key="power_factor_inverter_l2", name="Power Factor Inverter L2", device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),
    193: EG4ModbusSensorEntityDescription(key="power_factor_inverter_l3", name="Power Factor Inverter L3", device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, entity_registry_enabled_default=False),

    # --- Calculated Sensors ---
    -1: EG4ModbusSensorEntityDescription(key="power_pv_total", name="Power PV Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, icon="mdi:solar-power"),
    -2: EG4ModbusSensorEntityDescription(key="power_battery_total", name="Power Battery Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    -3: EG4ModbusSensorEntityDescription(key="energy_daily_pv_total", name="Energy Daily PV Total", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:solar-power"),
    -4: EG4ModbusSensorEntityDescription(key="energy_cumulative_pv", name="Energy Cumulative PV Total", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:solar-power"),
    -5: EG4ModbusSensorEntityDescription(key="energy_cumulative_grid_net", name="Energy Cumulative Grid Net", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:transmission-tower"),
    -6: EG4ModbusSensorEntityDescription(key="energy_daily_grid_net", name="Energy Daily Grid Net", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL, suggested_display_precision=1, icon="mdi:transmission-tower"),
    -7: EG4ModbusBinarySensorEntityDescription(key="inverter_time_accurate", name="Inverter Time Accurate", device_class=BinarySensorDeviceClass.CONNECTIVITY, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=True),
    -8: EG4ModbusSensorEntityDescription(key="parallel_master_slave", name="Parallel Master/Slave", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -9: EG4ModbusSensorEntityDescription(key="parallel_phase", name="Parallel Phase", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -10: EG4ModbusSensorEntityDescription(key="parallel_number", name="Parallel Number", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    -11: EG4ModbusSensorEntityDescription(key="power_grid_total", name="Power Grid Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:transmission-tower"),
    -12: EG4ModbusSensorEntityDescription(key="voltage_pv_average", name="Voltage PV Average", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1, icon="mdi:solar-panel-large"),
    -13: EG4ModbusSensorEntityDescription(key="inverter_uptime_days", name="Inverter Uptime", native_unit_of_measurement=UnitOfTime.DAYS, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    -14: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch1", name="AFCI Alarm CH1", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:alert"),
    -15: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch2", name="AFCI Alarm CH2", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:alert"),
    -16: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch3", name="AFCI Alarm CH3", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:alert"),
    -17: EG4ModbusBinarySensorEntityDescription(key="afci_alarm_ch4", name="AFCI Alarm CH4", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:alert"),
    -18: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch1", name="AFCI Self-Test CH1", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-check"),
    -19: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch2", name="AFCI Self-Test CH2", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-check"),
    -20: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch3", name="AFCI Self-Test CH3", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-check"),
    -21: EG4ModbusBinarySensorEntityDescription(key="afci_selftest_ch4", name="AFCI Self-Test CH4", device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:shield-check"),
}

# --- Holding Registers (Function Codes 0x03, 0x06, 0x10), ---
# A single dictionary for all holding registers. The setup process will determine
# whether to create a sensor, number, or select entity based on the description type.
HOLDING_REGISTERS: dict[int, Union[EG4ModbusSensorEntityDescription, EG4ModbusNumberEntityDescription, EG4ModbusSelectEntityDescription, EG4ModbusTimeEntityDescription]] = {
    9: EG4ModbusSensorEntityDescription(key="hardware_com_version", name="Hardware COM Version", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    10: EG4ModbusSensorEntityDescription(key="hardware_controller_version", name="Hardware Control Version", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
    16: EG4ModbusSelectEntityDescription(key="setting_language", name="Language", options=["Chinese", "English", "Spanish", "German"], icon="mdi:cog"),
    20: EG4ModbusSelectEntityDescription(key="setting_pv_input_model", name="PV Input Model", options=["No PV", "PV1", "PV2", "PV3", "PV1&2", "PV1&3", "PV2&3", "PV1&2&3"], icon="mdi:solar-power"),
    2101: EG4ModbusSelectEntityDescription(key="setting_func_en_eps", name="Inverter UPS / Power Backup", address=21, bit_mask=0x0001, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2102: EG4ModbusSelectEntityDescription(key="setting_func_en_ovf_load_derate", name="Over Frequency Load Reduction", address=21, bit_mask=0x0002, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:home-lightning-bolt"),
    2104: EG4ModbusSelectEntityDescription(key="setting_func_en_lvrt", name="Low Voltage Ride Through", address=21, bit_mask=0x0008, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2105: EG4ModbusSelectEntityDescription(key="setting_func_en_anti_island", name="Anti-islanding", address=21, bit_mask=0x0010, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2106: EG4ModbusSelectEntityDescription(key="setting_func_en_neutral_detect", name="Neutral Detect", address=21, bit_mask=0x0020, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2107: EG4ModbusSelectEntityDescription(key="setting_func_en_grid_on_power_ss", name="Seamless Switching when Grid On", address=21, bit_mask=0x0040, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:transmission-tower"),
    2108: EG4ModbusSelectEntityDescription(key="setting_func_en_ac_charge", name="AC Charge", address=21, bit_mask=0x0080, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:battery-charging-high"),
    2109: EG4ModbusSelectEntityDescription(key="setting_func_en_sw_seamlessly", name="Seamless Switching", address=21, bit_mask=0x0100, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2110: EG4ModbusSelectEntityDescription(key="setting_func_en_set_to_standby", name="Standby Mode", address=21, bit_mask=0x0200, options=["Standby", "Normal"], icon="mdi:toggle-switch-outline"),
    2111: EG4ModbusSelectEntityDescription(key="setting_func_en_forced_dischg", name="AC Forced Discharge", address=21, bit_mask=0x0400, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2112: EG4ModbusSelectEntityDescription(key="setting_func_en_forced_chg", name="AC Force Charge", address=21, bit_mask=0x0800, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2113: EG4ModbusSelectEntityDescription(key="setting_func_en_iso", name="Insulation Resistance Monitoring and Tripping", address=21, bit_mask=0x1000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2114: EG4ModbusSelectEntityDescription(key="setting_func_en_gfci", name="Ground Fault Circuit Monitoring and Tripping", address=21, bit_mask=0x2000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2115: EG4ModbusSelectEntityDescription(key="setting_func_en_dci", name="DC Injection Monitoring and Tripping", address=21, bit_mask=0x4000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2116: EG4ModbusSelectEntityDescription(key="setting_func_en_feed_in_grid", name="Grid Export", address=21, bit_mask=0x8000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:transmission-tower"),
    11000: EG4ModbusSelectEntityDescription(key="setting_functionen1_ubpvgridoffen", name="PV during Loss of Grid", address=110, bit_mask=0x0001, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11001: EG4ModbusSelectEntityDescription(key="setting_functionen1_ubfastzeroexport", name="Grid Fast Zero Export", address=110, bit_mask=0x0002, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11002: EG4ModbusSelectEntityDescription(key="setting_functionen1_ubmicrogriden", name="Micro Grid", address=110, bit_mask=0x0004, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11003: EG4ModbusSelectEntityDescription(key="setting_functionen1_ubbatshared", name="Battery is Shared", address=110, bit_mask=0x0008, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11004: EG4ModbusSelectEntityDescription(key="setting_functionen1_ubchglasten", name="Charge Last", address=110, bit_mask=0x0010, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11005: EG4ModbusSelectEntityDescription(key="setting_functionen1_ctsampleratio", name="CT Sample Ratio", address=110, bit_mask=0x0060, entity_category=None, options=["1/1000", "1/3000"], icon="mdi:cog"),
    11007: EG4ModbusSelectEntityDescription(key="setting_functionen1_buzzeren", name="Buzzer", address=110, bit_mask=0x0080, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11008: EG4ModbusSelectEntityDescription(key="setting_functionen1_pvctsampletype", name="PV CT Sample Type", address=110, bit_mask=0x0300, entity_category=None, options=["PV power", "SpecLoad"], icon="mdi:cog"),
    11010: EG4ModbusSelectEntityDescription(key="setting_functionen1_takeloadtogether", name="Take Load Together", address=110, bit_mask=0x0400, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11011: EG4ModbusSelectEntityDescription(key="setting_functionen1_ongridworkingmode", name="On Grid Working Mode", address=110, bit_mask=0x0800, entity_category=None, options=["Self consumption", "Charge First"], icon="mdi:cog"),
    11012: EG4ModbusSelectEntityDescription(key="setting_functionen1_pvctsampleratio", name="PV CT Sample Ratio", address=110, bit_mask=0x3000, entity_category=None, options=["1/1000", "1/3000"], icon="mdi:cog"),
    11014: EG4ModbusSelectEntityDescription(key="setting_functionen1_greenmodeen", name="Off Grid Simulation Mode", address=110, bit_mask=0x4000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    11015: EG4ModbusSelectEntityDescription(key="setting_functionen1_ecomodeen", name="Eco Mode", address=110, bit_mask=0x8000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    59: EG4ModbusSelectEntityDescription(key="setting_reactive_power_cmd_type", name="Reactive Power Command Type", options=["Unit power factor", "Fixed PF", "Default PF curve (Q(P))", "Custom PF curve", "Capacitive reactive power percentage", "Inductive reactive power percentage", "Q(V) curve", "Q(V) Dynamic"], icon="mdi:flash"),
    22: EG4ModbusNumberEntityDescription(key="setting_voltage_pv_start", name="PV Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=90, native_max_value=500, icon="mdi:solar-panel-large"),
    23: EG4ModbusNumberEntityDescription(key="setting_time_grid_connection_wait", name="Grid Connection Wait Time", native_unit_of_measurement=UnitOfTime.SECONDS, native_min_value=30, native_max_value=600, icon="mdi:transmission-tower"),
    24: EG4ModbusNumberEntityDescription(key="setting_time_grid_reconnection_wait", name="Grid Reconnection Wait Time", native_unit_of_measurement=UnitOfTime.SECONDS, native_min_value=0, native_max_value=900, icon="mdi:timer-sand"),
    64: EG4ModbusNumberEntityDescription(key="setting_percent_charge_power", name="Charge Power Percentage", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:battery-charging-high"),
    65: EG4ModbusNumberEntityDescription(key="setting_percent_discharge_power", name="Discharge Power Percentage", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:battery-charging-high"),
    66: EG4ModbusNumberEntityDescription(key="setting_percent_ac_charge_power", name="AC Charge Percentage", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:battery-charging-high"),
    67: EG4ModbusNumberEntityDescription(key="setting_limit_soc_ac_charge", name="AC Charging SOC Limit", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:battery-charging-high"),
    90: EG4ModbusSelectEntityDescription(key="setting_voltage_inverter", name="Inverter Voltage", options=["208 V", "220 V", "230 V", "240 V", "277 V"], option_dict={208: "208 V", 220: "220 V", 230: "230 V", 240: "240 V", 277: "277 V"}, icon="mdi:sine-wave"),
    91: EG4ModbusSelectEntityDescription(key="setting_frequency_inverter", name="Inverter Frequency", options=["50 Hz", "60 Hz"], option_dict={50: "50 Hz", 60: "60 Hz"}, icon="mdi:cog"),
    99: EG4ModbusNumberEntityDescription(key="setting_voltage_charge_ref", name="Charge Voltage Reference", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=50, native_max_value=59, icon="mdi:battery-charging-high"),
    100: EG4ModbusNumberEntityDescription(key="setting_voltage_discharge_cutoff", name="Discharge Cutoff Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=50, icon="mdi:battery-charging-high"),
    101: EG4ModbusNumberEntityDescription(key="setting_current_charge", name="Charge Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, native_min_value=0, native_max_value=140, icon="mdi:battery-charging-high"),
    102: EG4ModbusNumberEntityDescription(key="setting_current_discharge", name="Discharge Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, native_min_value=0, native_max_value=140, icon="mdi:battery-charging-high"),
    103: EG4ModbusNumberEntityDescription(key="setting_max_backflow_power", name="Grid Export Power Limit", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:flash"),
    105: EG4ModbusNumberEntityDescription(key="setting_eod_soc", name="EOD SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=10, native_max_value=90, icon="mdi:cog"),
    112: EG4ModbusSelectEntityDescription(key="setting_system_type", name="System Type", options=["No Parallel", "Parallel - Master - Single Phase", "Slave", "Parallel - Master - Three Phase"], icon="mdi:cog"),
    113: EG4ModbusSelectEntityDescription(key="setting_composed_phase", name="Off-grid Composed Phase", options=["R Phase", "S Phase", "T Phase"], option_dict={1: "R Phase", 2: "S Phase", 3: "T Phase"}, icon="mdi:chart-timeline-variant"),
    116: EG4ModbusNumberEntityDescription(key="setting_ptouser_start_discharge", name="Ptouser Start Discharge", native_unit_of_measurement=UnitOfPower.WATT, native_min_value=50, native_max_value=10000, icon="mdi:battery-charging-high"),
    118: EG4ModbusNumberEntityDescription(key="setting_voltage_start_derating", name="Voltage Start Derating", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, icon="mdi:sine-wave"),
    119: EG4ModbusNumberEntityDescription(key="setting_power_offset_wct", name="Power Offset WCT", native_unit_of_measurement=UnitOfPower.WATT, native_min_value=-1000, native_max_value=1000, icon="mdi:flash"),
    1201: EG4ModbusSelectEntityDescription(key="setting_ac_charge_type", name="AC Charge Type", address=120, bit_mask=0x000E, options=["Disable", "According to Time", "According to Voltage", "According to SOC", "According to Voltage and Time", "According to SOC and Time"], icon="mdi:battery-charging"),
    1202: EG4ModbusSelectEntityDescription(key="setting_discharge_control_type", name="Discharge Control Type", address=120, bit_mask=0x0030, options=["According to Voltage", "According to SOC", "According to Both"], icon="mdi:battery-arrow-down"),
    1203: EG4ModbusSelectEntityDescription(key="setting_ongrid_eod_type", name="On-Grid EOD Type", address=120, bit_mask=0x0040, options=["According to Voltage", "According to SOC"], icon="mdi:transmission-tower"),
    1204: EG4ModbusSelectEntityDescription(key="setting_generator_charge_type", name="Generator Charge Type", address=120, bit_mask=0x0080, options=["According to Battery Voltage", "According to Battery SOC"], icon="mdi:generator-portable"),
    125: EG4ModbusNumberEntityDescription(key="setting_soc_low_limit_inverter_discharge", name="SOC Low Limit Inverter Discharge", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:battery-charging-high"),
    1261: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_0", name="Hourly Charge Discharge 00 - 0:00-0:30", address=126, bit_mask=0x03, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1262: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_1", name="Hourly Charge Discharge 01 - 8:30-9:00", address=126, bit_mask=0x0C, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1263: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_2", name="Hourly Charge Discharge 02 - 9:00-9:30", address=126, bit_mask=0x30, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1264: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_3", name="Hourly Charge Discharge 03 - 9:30-10:00", address=126, bit_mask=0xC0, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1265: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_4", name="Hourly Charge Discharge 04 - 10:00-10:30", address=126, bit_mask=0x300, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1266: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_5", name="Hourly Charge Discharge 05 - 10:30-11:00", address=126, bit_mask=0xC00, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1267: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_6", name="Hourly Charge Discharge 06 - 11:00-11:30", address=126, bit_mask=0x3000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1268: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_7", name="Hourly Charge Discharge 07 - 11:30-12:00", address=126, bit_mask=0xC000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1271: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_8", name="Hourly Charge Discharge 08 - 8:00-8:30", address=127, bit_mask=0x03, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1272: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_9", name="Hourly Charge Discharge 09 - 8:30-9:00", address=127, bit_mask=0x0C, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1273: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_10", name="Hourly Charge Discharge 10 - 9:00-9:30", address=127, bit_mask=0x30, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1274: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_11", name="Hourly Charge Discharge 11 - 5:30-6:00", address=127, bit_mask=0xC0, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1275: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_12", name="Hourly Charge Discharge 12 - 6:00-6:30", address=127, bit_mask=0x300, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1276: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_13", name="Hourly Charge Discharge 13 - 6:30-7:00", address=127, bit_mask=0xC00, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1277: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_14", name="Hourly Charge Discharge 14 - 7:00-7:30", address=127, bit_mask=0x3000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1278: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_15", name="Hourly Charge Discharge 15 - 7:30-8:00", address=127, bit_mask=0xC000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1281: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_16", name="Hourly Charge Discharge 16 - 8:00-8:30", address=128, bit_mask=0x03, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1282: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_17", name="Hourly Charge Discharge 17 - 8:30-9:00", address=128, bit_mask=0x0C, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1283: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_18", name="Hourly Charge Discharge 18 - 9:00-9:30", address=128, bit_mask=0x30, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1284: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_19", name="Hourly Charge Discharge 19 - 9:30-10:00", address=128, bit_mask=0xC0, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1285: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_20", name="Hourly Charge Discharge 20 - 10:00-10:30", address=128, bit_mask=0x300, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1286: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_21", name="Hourly Charge Discharge 21 - 10:30-11:00", address=128, bit_mask=0xC00, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1287: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_22", name="Hourly Charge Discharge 22 - 11:00-11:30", address=128, bit_mask=0x3000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1288: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_23", name="Hourly Charge Discharge 23 - 11:30-12:00", address=128, bit_mask=0xC000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1291: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_24", name="Hourly Charge Discharge 24 - 12:00-12:30", address=129, bit_mask=0x03, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1292: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_25", name="Hourly Charge Discharge 25 - 12:30-13:00", address=129, bit_mask=0x0C, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1293: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_26", name="Hourly Charge Discharge 26 - 13:00-13:30", address=129, bit_mask=0x30, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1294: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_27", name="Hourly Charge Discharge 27 - 13:30-14:00", address=129, bit_mask=0xC0, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1295: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_28", name="Hourly Charge Discharge 28 - 14:00-14:30", address=129, bit_mask=0x300, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1296: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_29", name="Hourly Charge Discharge 29 - 14:30-15:00", address=129, bit_mask=0xC00, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1297: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_30", name="Hourly Charge Discharge 30 - 15:00-15:30", address=129, bit_mask=0x3000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1298: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_31", name="Hourly Charge Discharge 31 - 15:30-16:00", address=129, bit_mask=0xC000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1301: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_32", name="Hourly Charge Discharge 32 - 16:00-16:30", address=130, bit_mask=0x03, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1302: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_33", name="Hourly Charge Discharge 33 - 16:30-17:00", address=130, bit_mask=0x0C, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1303: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_34", name="Hourly Charge Discharge 34 - 17:00-17:30", address=130, bit_mask=0x30, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1304: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_35", name="Hourly Charge Discharge 35 - 17:30-18:00", address=130, bit_mask=0xC0, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1305: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_36", name="Hourly Charge Discharge 36 - 18:00-18:30", address=130, bit_mask=0x300, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1306: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_37", name="Hourly Charge Discharge 37 - 18:30-19:00", address=130, bit_mask=0xC00, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1307: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_38", name="Hourly Charge Discharge 38 - 19:00-19:30", address=130, bit_mask=0x3000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1308: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_39", name="Hourly Charge Discharge 39 - 19:30-20:00", address=130, bit_mask=0xC000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1311: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_40", name="Hourly Charge Discharge 40 - 20:00-20:30", address=131, bit_mask=0x03, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1312: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_41", name="Hourly Charge Discharge 41 - 20:30-21:00", address=131, bit_mask=0x0C, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1313: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_42", name="Hourly Charge Discharge 42 - 21:00-21:30", address=131, bit_mask=0x30, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1314: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_43", name="Hourly Charge Discharge 43 - 21:30-22:00", address=131, bit_mask=0xC0, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1315: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_44", name="Hourly Charge Discharge 44 - 22:00-22:30", address=131, bit_mask=0x300, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1316: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_45", name="Hourly Charge Discharge 45 - 22:30-23:00", address=131, bit_mask=0xC00, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1317: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_46", name="Hourly Charge Discharge 46 - 23:00-23:30", address=131, bit_mask=0x3000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    1318: EG4ModbusSelectEntityDescription(key="setting_hourly_charge_discharge_time_47", name="Hourly Charge Discharge 47 - 23:30-0:00", address=131, bit_mask=0xC000, options=["No action", "Charging", "Discharging"], entity_registry_visible_default=False, entity_registry_enabled_default=False, icon="mdi:clock-outline"),
    144: EG4ModbusNumberEntityDescription(key="setting_voltage_float_charge", name="Float Charge Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=50, native_max_value=56, icon="mdi:battery-charging-high"),
    145: EG4ModbusSelectEntityDescription(key="setting_output_priority_config", name="Output Priority Config", options=["Battery First", "PV First", "AC First"], icon="mdi:home-lightning-bolt"),
    146: EG4ModbusSelectEntityDescription(key="setting_line_mode", name="Grid Transfer Mode", options=["APL (90-280V with 20ms transfer)", "UPS (170-280V with 10ms transfer)", "GEN (90-280V with 20ms transfer)"], icon="mdi:cog"),
    147: EG4ModbusSensorEntityDescription(key="setting_battery_capacity", name="Battery Capacity Setting", native_unit_of_measurement="Ah", state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:cog"),
    148: EG4ModbusNumberEntityDescription(key="setting_battery_nominal_voltage", name="Battery Nominal Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=59, icon="mdi:cog"),
    149: EG4ModbusNumberEntityDescription(key="setting_voltage_equalization", name="Equalization Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=50, native_max_value=59, icon="mdi:sine-wave"),
    150: EG4ModbusNumberEntityDescription(key="setting_equalization_interval", name="Equalization Interval", native_unit_of_measurement=UnitOfTime.DAYS, native_min_value=0, native_max_value=365, icon="mdi:cog"),
    151: EG4ModbusNumberEntityDescription(key="setting_equalization_time", name="Equalization Time", native_unit_of_measurement=UnitOfTime.HOURS, native_min_value=0, native_max_value=24, icon="mdi:timer-sand"),
    158: EG4ModbusNumberEntityDescription(key="setting_voltage_ac_charge_start", name="AC Charge Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=38.4, native_max_value=52, icon="mdi:battery-charging-high"),
    159: EG4ModbusNumberEntityDescription(key="setting_voltage_ac_charge_end", name="AC Charge End Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=48, native_max_value=59, icon="mdi:battery-charging-high"),
    160: EG4ModbusNumberEntityDescription(key="setting_soc_ac_charge_start", name="AC Charge Start SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=90, icon="mdi:battery-charging-high"),
    161: EG4ModbusNumberEntityDescription(key="setting_soc_ac_charge_end", name="AC Charge End SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=20, native_max_value=100, icon="mdi:battery-charging-high"),
    162: EG4ModbusNumberEntityDescription(key="setting_voltage_battery_low", name="Battery Low Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=50, icon="mdi:cog"),
    163: EG4ModbusNumberEntityDescription(key="setting_voltage_battery_low_back", name="Battery Low Back Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=42, native_max_value=52, icon="mdi:cog"),
    164: EG4ModbusNumberEntityDescription(key="setting_soc_battery_low", name="Battery Low SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=90, icon="mdi:cog"),
    165: EG4ModbusNumberEntityDescription(key="setting_soc_battery_low_back", name="Battery Low Back SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=20, native_max_value=100, icon="mdi:cog"),
    166: EG4ModbusNumberEntityDescription(key="setting_voltage_battery_low_to_utility", name="Battery Low to Utility Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=44.4, native_max_value=51.4, icon="mdi:cog"),
    167: EG4ModbusNumberEntityDescription(key="setting_soc_battery_low_to_utility", name="Battery Low to Utility SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:cog"),
    168: EG4ModbusNumberEntityDescription(key="setting_current_ac_charge_battery", name="AC Charge Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, native_min_value=0, native_max_value=140, icon="mdi:battery-charging-high"),
    169: EG4ModbusNumberEntityDescription(key="setting_voltage_ongrid_eod", name="Ongrid EOD Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=56, icon="mdi:transmission-tower"),
    176: EG4ModbusNumberEntityDescription(key="setting_power_max_grid_input", name="Max Grid Input Power", native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:transmission-tower"),
    177: EG4ModbusNumberEntityDescription(key="setting_power_gen_rated", name="Gen Rated Power", native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:generator-portable"),
    17907: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_grid_peak_shaving", name="Grid Peak Shaving", address=179, bit_mask=0x80, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:transmission-tower"),
    17908: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_gen_peak_shaving", name="Gen Peak Shaving", address=179, bit_mask=0x100, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:generator-portable"),
    17909: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_bat_chg_control", name="Battery Charge Control", address=179, bit_mask=0x200, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    17910: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_bat_dischg_control", name="Battery Discharge Control", address=179, bit_mask=0x400, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    17911: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_ac_coupling", name="AC Coupling", address=179, bit_mask=0x800, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    17912: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_pv_arc_en", name="PV Arc Detection", address=179, bit_mask=0x1000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:solar-power"),
    17913: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_smart_load_en", name="Aux Port Use", address=179, bit_mask=0x2000, entity_category=None, options=["Generator", "Smart Load"], icon="mdi:home-lightning-bolt"),
    17914: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_rsd_disable", name="RSD", address=179, bit_mask=0x4000, entity_category=None, options=["Enabled", "Disabled"], icon="mdi:cog"),  ## REVERSING DOUBLE NEGATIVE
    17915: EG4ModbusSelectEntityDescription(key="setting_ufunctionen2_ongrid_always_on", name="Smart Load Ongrid Always On", address=179, bit_mask=0x8000, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:transmission-tower"),


    194: EG4ModbusNumberEntityDescription(key="setting_voltage_gen_charge_start", name="Gen Charge Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=38.4, native_max_value=52, icon="mdi:generator-portable"),
    195: EG4ModbusNumberEntityDescription(key="setting_voltage_gen_charge_end", name="Gen Charge End Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=48, native_max_value=59, icon="mdi:generator-portable"),
    196: EG4ModbusNumberEntityDescription(key="setting_soc_gen_charge_start", name="Gen Charge Start SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=90, icon="mdi:generator-portable"),
    197: EG4ModbusNumberEntityDescription(key="setting_soc_gen_charge_end", name="Gen Charge End SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=20, native_max_value=100, icon="mdi:generator-portable"),
    198: EG4ModbusNumberEntityDescription(key="setting_current_max_gen_charge_battery", name="Max Gen Charge Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, native_min_value=0, native_max_value=60, icon="mdi:generator-portable"),

    199: EG4ModbusNumberEntityDescription(key="setting_over_temp_derate_point", name="Over Temp Derate Point", native_unit_of_measurement=UnitOfTemperature.CELSIUS, scale=0.1, native_min_value=60, native_max_value=90, icon="mdi:cog"),
    201: EG4ModbusNumberEntityDescription(key="setting_chg_first_end_volt", name="Charge Priority Voltage Limit", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=48, native_max_value=59, icon="mdi:cog"),
    202: EG4ModbusNumberEntityDescription(key="setting_force_dischg_end_volt", name="Forced Discharge Voltage Limit", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=56, icon="mdi:cog"),
    # 203: EG4ModbusSelectEntityDescription(key="setting_grid_regulation", name="Grid Regulation", options=["1", "2", "3"], icon="mdi:transmission-tower"), ## OPTIONS UNKNOWN
    204: EG4ModbusNumberEntityDescription(key="setting_lead_capacity", name="Lead Capacity", native_unit_of_measurement="Ah", native_min_value=50, native_max_value=850, icon="mdi:cog"),
    205: EG4ModbusSelectEntityDescription(key="setting_grid_type", name="Grid Type", options=["Split 240V", "Split 208V", "Single 240V", "Single 230V", "Split 200V"], icon="mdi:transmission-tower"),
    206: EG4ModbusNumberEntityDescription(key="setting_peak_shaving_power", name="Peak Shaving Power", native_unit_of_measurement=UnitOfPower.KILO_WATT, scale=0.1, native_min_value=0, native_max_value=25.5, icon="mdi:flash"),
    207: EG4ModbusNumberEntityDescription(key="setting_peak_shaving_a_soc", name="Peak Shaving A SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:cog"),
    208: EG4ModbusNumberEntityDescription(key="setting_peak_shaving_a_volt", name="Peak Shaving A Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=48, native_max_value=59, icon="mdi:cog"),
    209: EG4ModbusTimeEntityDescription(key="setting_peak_shaving_a_start", name="Peak Shaving A Start Time", address=209, icon="mdi:cog"),
    210: EG4ModbusTimeEntityDescription(key="setting_peak_shaving_a_end", name="Peak Shaving A End Time", address=210, icon="mdi:cog"),
    211: EG4ModbusTimeEntityDescription(key="setting_peak_shaving_b_start", name="Peak Shaving B Start Time", address=211, icon="mdi:cog"),
    212: EG4ModbusTimeEntityDescription(key="setting_peak_shaving_b_end", name="Peak Shaving B End Time", address=212, icon="mdi:cog"),
    213: EG4ModbusNumberEntityDescription(key="setting_smart_load_on_volt", name="Smart Load On Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=48, native_max_value=59, icon="mdi:home-lightning-bolt"),
    214: EG4ModbusNumberEntityDescription(key="setting_smart_load_off_volt", name="Smart Load Off Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=52, icon="mdi:home-lightning-bolt"),
    215: EG4ModbusNumberEntityDescription(key="setting_smart_load_on_soc", name="Smart Load On SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:home-lightning-bolt"),
    216: EG4ModbusNumberEntityDescription(key="setting_smart_load_off_soc", name="Smart Load Off SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:home-lightning-bolt"),
    217: EG4ModbusNumberEntityDescription(key="setting_start_pv_power", name="Start PV Power", native_unit_of_measurement=UnitOfPower.KILO_WATT, scale=0.1, native_min_value=0, native_max_value=12, icon="mdi:solar-power"),
    218: EG4ModbusNumberEntityDescription(key="setting_peak_shaving_b_soc", name="Peak Shaving B SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:cog"),
    219: EG4ModbusNumberEntityDescription(key="setting_peak_shaving_b_volt", name="Peak Shaving B Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=48, native_max_value=59, icon="mdi:cog"),
    220: EG4ModbusNumberEntityDescription(key="setting_ac_couple_start_soc", name="AC Couple Start SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=80, icon="mdi:cog"),
    221: EG4ModbusNumberEntityDescription(key="setting_ac_couple_end_soc", name="AC Couple End SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=0, native_max_value=100, icon="mdi:cog"),
    222: EG4ModbusNumberEntityDescription(key="setting_ac_couple_start_volt", name="AC Couple Start Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=52, icon="mdi:cog"),
    223: EG4ModbusNumberEntityDescription(key="setting_ac_couple_end_volt", name="AC Couple End Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=56, icon="mdi:cog"),
    2241: EG4ModbusSensorEntityDescription(key="hardware_lcd_version", name="Hardware Display Version", address=224, bit_mask=0xFF),
    2242: EG4ModbusSensorEntityDescription(key="hardware_lcd_screen_type", name="Hardware Display Type", address=224, bit_mask=0x300),
    2243: EG4ModbusSensorEntityDescription(key="hardware_lcd_model_code", name="Hardware Display Model Code", address=224, bit_mask=0xFC00), # 0xFC00 = bits 10-15$6
    2261: EG4ModbusSelectEntityDescription(key="setting_func3_exct_en", name="External CT", address=226, bit_mask=0x4, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog"),
    2262: EG4ModbusSelectEntityDescription(key="setting_func3_runwithoutgrid", name="Run Without Grid", address=226, bit_mask=0x8, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:transmission-tower"),
    2263: EG4ModbusSelectEntityDescription(key="setting_func3_nperlyen", name="Neutral to Ground Relay", address=226, bit_mask=0x10, entity_category=None, options=["Disabled", "Enabled"], icon="mdi:cog", entity_registry_visible_default=False),
    227: EG4ModbusNumberEntityDescription(key="setting_bat_stop_charge_soc", name="Battery Stop Charge SOC", native_unit_of_measurement=PERCENTAGE, native_min_value=10, native_max_value=101, icon="mdi:battery-charging-high"),
    228: EG4ModbusNumberEntityDescription(key="setting_bat_stop_charge_volt", name="Battery Stop Charge Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, scale=0.1, native_min_value=40, native_max_value=59.5, icon="mdi:battery-charging-high"),
}


# --- Enums and Flags ---
INVERTER_STATUS_CODES = {
    0x00: "Standby", 0x01: "Fault", 0x02: "Programming", 0x04: "ON GRID: PV",
    0x08: "PV Charge", 0x0C: "ON GRID: PV Charge", 0x10: "ON GRID: Battery",
    0x14: "ON GRID: PV + Battery", 0x20: "AC Charge", 0x28: "PV + AC Charge",
    0x40: "OFF GRID: Battery", 0x80: "OFF GRID: PV", 0x88: "OFF GRID: PV Charge",
    0xC0: "OFF GRID: PV + Battery",
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
    (1 << 20): "Inverter connection fault", (1 << 21): "PV Voltage high", (1 << 22): "Over current protection",
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
    (1 << 27): "Battery open circuit", (1 << 28): "Inverter overload", (1 << 29): "Inverter voltage high",
    (1 << 30): "Meter reverse connection", (1 << 31): "DCV high",
}