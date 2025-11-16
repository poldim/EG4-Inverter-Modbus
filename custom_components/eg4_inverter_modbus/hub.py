"""EG4 Modbus Hub"""
from datetime import datetime, timedelta, timezone
import inspect
import logging
import struct
import threading
from typing import Optional

from homeassistant.core import CALLBACK_TYPE, callback, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

import pymodbus
from pymodbus import __version__ as pymodbus_version
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from pymodbus.pdu import ExceptionResponse
from packaging.version import parse as parse_version

from .const import (
    FAULT_CODES,
    WARNING_CODES,
    INVERTER_STATUS_CODES,
    AC_INPUT_TYPE_CODES,
)

_LOGGER = logging.getLogger(__name__)


class CustomPayloadDecoder:
    """
    A custom decoder that operates directly on a list of registers
    to replace the deprecated BinaryPayloadDecoder.
    """
    def __init__(self, registers: list[int]):
        """Initialize the decoder with a list of registers."""
        self._registers = registers
        self._pointer = 0

    def _check_index(self, count: int):
        """Check if there are enough registers left to decode."""
        if self._pointer + count > len(self._registers):
            _LOGGER.warning(f"Not enough registers to decode. Have {len(self._registers)}, need {self._pointer + count}")
            raise IndexError("Not enough registers to decode")

    def decode_16bit_uint(self) -> int:
        """Decode a 16-bit unsigned integer from one register."""
        self._check_index(1)
        val = self._registers[self._pointer]
        self._pointer += 1
        return val

    def decode_16bit_int(self) -> int:
        """Decode a 16-bit signed integer from one register."""
        self._check_index(1)
        val = self._registers[self._pointer]
        self._pointer += 1
        if val & 0x8000:
            return val - 0x10000
        return val

    def decode_32bit_uint(self) -> int:
        """Decode a 32-bit unsigned integer from two registers."""
        self._check_index(2)
        low_word = self._registers[self._pointer]
        high_word = self._registers[self._pointer + 1]
        self._pointer += 2
        return (high_word << 16) | low_word
    
    def decode_32bit_int(self) -> int:
        """Decode a 32-bit signed integer from two registers."""
        val = self.decode_32bit_uint()
        if val & 0x80000000:
            return val - 0x100000000
        return val

    def skip_registers(self, count: int) -> None:
        """Skip a number of registers in the payload."""
        self._pointer += count


class EG4ModbusHub(DataUpdateCoordinator[dict]):
    """Thread safe wrapper class for pymodbus."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        port: int,
        slave: int,
        scan_interval: int,
    ):
        """Initialize the Modbus hub."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = ModbusTcpClient(host=host, port=port, timeout=5)
        self._device_id = slave if slave else 1
        self._lock = threading.Lock()
        self.data: dict = {}
        
        self._pyversion = parse_version(pymodbus_version)

        possible_kwarg_names = ("slave", "unit", "device_id")

        def _detect_kwarg(method_name: str) -> Optional[str]:
            method = getattr(self._client, method_name, None)
            if method is None:
                return None
            try:
                parameters = inspect.signature(method).parameters
            except (ValueError, TypeError):
                return None
            for candidate in possible_kwarg_names:
                if candidate in parameters:
                    return candidate
            return None

        detected_kwarg = _detect_kwarg("read_input_registers")
        if detected_kwarg is None:
            detected_kwarg = _detect_kwarg("write_register")

        if detected_kwarg is None:
            detected_kwarg = "slave"
            _LOGGER.warning(
                "Could not auto-detect pymodbus unit keyword argument for version %s. "
                "Falling back to '%s'.", self._pyversion, detected_kwarg
            )

        self._kwargs = {detected_kwarg: self._device_id}

        _LOGGER.info(
            "Pymodbus version %s detected. Using keyword argument '%s' with unit id %s",
            self._pyversion,
            detected_kwarg,
            self._device_id,
        )

    @callback
    def async_remove_listener(self, update_callback: CALLBACK_TYPE) -> None:
        """Remove data update listener."""
        super().async_remove_listener(update_callback)
        if not self._listeners:
            self.close()

    def close(self) -> None:
        """Disconnect client."""
        with self._lock:
            if self._client.is_socket_open():
                self._client.close()

    def write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        if self._kwargs is None:
            _LOGGER.error("Cannot write register: integration has not successfully polled yet. Please wait.")
            return False

        with self._lock:
            try:
                with self._client as client:
                    if not client.is_socket_open():
                        client.connect() # Ensure connection
                    
                    if not client.is_socket_open():
                        _LOGGER.error("Client connection failed before write.")
                        return False
                        
                    result = client.write_register(address=address, value=value, **self._kwargs)
                    
                    if result.isError():
                        _LOGGER.error(f"Error writing register {address} with value {value}: {result}")
                        return False
                    return True
            except ConnectionException as ex:
                _LOGGER.error(f"Connection failed during write: {ex}")
                return False
            except Exception as e:
                _LOGGER.error(f"An unexpected error occurred during Modbus write: {e}")
                return False

    async def _async_update_data(self) -> dict:
        """Fetch data from inverter in a single executor job."""
        return await self.hass.async_add_executor_job(self._sync_update_data)

    def _sync_update_data(self) -> dict:
        """
        Synchronously read all Modbus data in a single session.
        This runs in the executor and performs all I/O,
        preventing multiple sequential connections.
        """
        data = self.data.copy()
        updated = False

        with self._lock:
            try:
                with self._client as client:
                    if not client.is_socket_open():
                        client.connect() # Ensure connection

                    if not client.is_socket_open():
                        _LOGGER.error("Modbus connection failed")
                        return self.data # Return last known data on connection fail

                    # =================================================================================
                    # Read Input Registers (Function Code 0x04)
                    # =================================================================================
                    
                    # --- Block 1: Registers 0-39 ---
                    result = client.read_input_registers(0, count=40, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["inverter_state"] = INVERTER_STATUS_CODES.get(decoder.decode_16bit_uint(), "Unknown")
                        data["voltage_pv1"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_pv2"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_pv3"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_battery"] = decoder.decode_16bit_uint() / 10.0
                        soc_soh_register = decoder.decode_16bit_uint()
                        data["battery_soc"] = soc_soh_register & 0xFF
                        data["battery_soh"] = soc_soh_register >> 8
                        decoder.skip_registers(1)
                        data["power_pv1"] = decoder.decode_16bit_uint()
                        data["power_pv2"] = decoder.decode_16bit_uint()
                        data["power_pv3"] = decoder.decode_16bit_uint()
                        data["power_battery_charge"] = decoder.decode_16bit_uint()
                        data["power_battery_discharge"] = decoder.decode_16bit_uint()
                        data["voltage_grid_l1l2"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_grid_l2l3"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_grid_l3l1"] = decoder.decode_16bit_uint() / 10.0
                        
                        fac_pinv_reg = decoder.decode_16bit_uint()
                        data["frequency_grid"] = (fac_pinv_reg) / 100.0
                        data["power_inverter_output"] = decoder.decode_16bit_uint()
                        data["power_ac_charge"] = decoder.decode_16bit_uint()
                        data["current_inverter_rms"] = decoder.decode_16bit_uint() / 100.0
                        data["power_factor_inverter"] = decoder.decode_16bit_uint() / 1000.0
                        data["voltage_inverter_l1l2"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_inverter_l2l3"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_inverter_l3l1"] = decoder.decode_16bit_uint() / 10.0
                        data["frequency_inverter"] = decoder.decode_16bit_uint() / 100.0
                        data["power_inverter"] = decoder.decode_16bit_uint()
                        data["power_apparent_inverter"] = decoder.decode_16bit_uint()
                        data["power_grid_export"] = decoder.decode_16bit_uint()
                        data["power_grid_import"] = decoder.decode_16bit_uint()
                        data["energy_daily_pv1"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_pv2"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_pv3"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_inverter_output"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_ac_charge"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_battery_charge"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_battery_discharge"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_inverter"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_grid_export"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_grid_import"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_bus_1"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_bus_2"] = decoder.decode_16bit_uint() / 10.0
                    else:
                        _LOGGER.warning("Modbus read error on input registers 0-39")

                    # --- Block 2: Registers 40-79 ---
                    result = client.read_input_registers(40, count=40, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["energy_cumulative_pv1"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_pv2"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_pv3"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_inverter_output"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_ac_charge"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_battery_charge"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_battery_discharge"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_inverter"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_grid_export"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_grid_import"] = decoder.decode_32bit_uint() / 10.0
                        
                        fault_code_val = decoder.decode_32bit_uint()
                        warning_code_val = decoder.decode_32bit_uint()
                        data["fault_code"] = self.translate_bitmask_to_messages(fault_code_val, FAULT_CODES)
                        data["warning_code"] = self.translate_bitmask_to_messages(warning_code_val, WARNING_CODES)

                        data["temperature_internal"] = decoder.decode_16bit_int()
                        data["temperature_heatsink_dc"] = decoder.decode_16bit_int()
                        data["temperature_heatsink_ac"] = decoder.decode_16bit_int()
                        data["temperature_battery"] = decoder.decode_16bit_int()
                        decoder.skip_registers(1)
                        
                        time_running_total_seconds = decoder.decode_32bit_uint()
                        current_time = datetime.now(timezone.utc)
                        data["inverter_on_time"] = (current_time - timedelta(seconds=time_running_total_seconds))
                        
                        auto_test_reg = decoder.decode_16bit_uint()
                        data["auto_test_status"] = (auto_test_reg >> 4) & 0x0F
                        decoder.skip_registers(5)
                        
                        ac_type_raw = decoder.decode_16bit_uint()
                        ac_type_val = ac_type_raw & 1
                        data["ac_input_type"] = AC_INPUT_TYPE_CODES.get(ac_type_val, "Unknown")
                        
                        decoder.skip_registers(2)
                    else:
                        _LOGGER.warning("Modbus read error on input registers 40-79")

                    # --- Block 3: Registers 80-119 ---
                    result = client.read_input_registers(80, count=40, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        decoder.skip_registers(1)
                        data["bms_current_max_charge"] = decoder.decode_16bit_uint() / 100.0
                        data["bms_current_max_discharge"] = decoder.decode_16bit_uint() / 100.0
                        data["bms_voltage_charge_ref"] = decoder.decode_16bit_uint() / 10.0
                        data["bms_voltage_discharge_cutoff"] = decoder.decode_16bit_uint() / 10.0
                        data["bms_status_0"] = decoder.decode_16bit_uint()
                        data["bms_status_1"] = decoder.decode_16bit_uint()
                        data["bms_status_2"] = decoder.decode_16bit_uint()
                        data["bms_status_3"] = decoder.decode_16bit_uint()
                        data["bms_status_4"] = decoder.decode_16bit_uint()
                        data["bms_status_5"] = decoder.decode_16bit_uint()
                        data["bms_status_6"] = decoder.decode_16bit_uint()
                        data["bms_status_7"] = decoder.decode_16bit_uint()
                        data["bms_status_8"] = decoder.decode_16bit_uint()
                        data["bms_status_9"] = decoder.decode_16bit_uint()
                        data["bms_status_inv"] = decoder.decode_16bit_uint()
                        data["battery_parallel_num"] = decoder.decode_16bit_uint()
                        data["battery_capacity_ah"] = decoder.decode_16bit_uint()
                        data["bms_current_battery"] = decoder.decode_16bit_int() / 10.0
                        data["bms_fault_code"] = decoder.decode_16bit_uint()
                        data["bms_warning_code"] = decoder.decode_16bit_uint()
                        data["bms_voltage_max_cell"] = decoder.decode_16bit_uint() / 1000.0
                        data["bms_voltage_min_cell"] = decoder.decode_16bit_uint() / 1000.0
                        data["bms_temperature_max_cell"] = decoder.decode_16bit_int() / 10.0
                        data["bms_temperature_min_cell"] = decoder.decode_16bit_int() / 10.0
                        data["bms_fw_update_state"] = decoder.decode_16bit_uint()
                        data["bms_cycle_count"] = decoder.decode_16bit_uint()
                        data["voltage_battery_sample_inverter"] = decoder.decode_16bit_uint() / 10.0
                        data["temperature_t1"] = decoder.decode_16bit_int() / 10.0
                        data["temperature_t2"] = decoder.decode_16bit_int() / 10.0
                        data["temperature_t3"] = decoder.decode_16bit_int() / 10.0
                        data["temperature_t4"] = decoder.decode_16bit_int() / 10.0
                        data["temperature_t5"] = decoder.decode_16bit_int() / 10.0
                        parallel_reg = decoder.decode_16bit_uint()
                        data["parallel_master_slave"] = parallel_reg & 0x03
                        data["parallel_phase"] = (parallel_reg >> 2) & 0x03
                        data["parallel_number"] = parallel_reg >> 8
                        decoder.skip_registers(6)
                    else:
                        _LOGGER.warning("Modbus read error on input registers 80-119")

                    # --- Block 4: Registers 120-152 ---
                    result = client.read_input_registers(120, count=33, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["voltage_bus_p"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_generator"] = decoder.decode_16bit_uint() / 10.0
                        data["frequency_generator"] = decoder.decode_16bit_uint() / 100.0
                        data["power_generator"] = decoder.decode_16bit_uint()
                        data["energy_daily_generator"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_cumulative_generator"] = decoder.decode_32bit_uint() / 10.0
                        data["voltage_inverter_l1n"] = decoder.decode_16bit_uint() / 10.0
                        data["voltage_inverter_l2n"] = decoder.decode_16bit_uint() / 10.0
                        data["power_inverter_l1n"] = decoder.decode_16bit_uint()
                        data["power_inverter_l2n"] = decoder.decode_16bit_uint()
                        data["power_apparent_inverter_l1n"] = decoder.decode_16bit_uint()
                        data["power_apparent_inverter_l2n"] = decoder.decode_16bit_uint()
                        data["energy_daily_inverter_l1n"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_daily_inverter_l2n"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_cumulative_inverter_l1n"] = decoder.decode_32bit_uint() / 10.0
                        data["energy_cumulative_inverter_l2n"] = decoder.decode_32bit_uint() / 10.0
                        decoder.skip_registers(1)
                        data["current_afci_ch1"] = decoder.decode_16bit_uint() / 10.0
                        data["current_afci_ch2"] = decoder.decode_16bit_uint() / 10.0
                        data["current_afci_ch3"] = decoder.decode_16bit_uint() / 10.0
                        data["current_afci_ch4"] = decoder.decode_16bit_uint() / 10.0
                        
                        reg_144 = decoder.decode_16bit_uint()
                        data["afci_alarm_ch1"] = bool(reg_144 & (1 << 0))
                        data["afci_alarm_ch2"] = bool(reg_144 & (1 << 1))
                        data["afci_alarm_ch3"] = bool(reg_144 & (1 << 2))
                        data["afci_alarm_ch4"] = bool(reg_144 & (1 << 3))
                        data["afci_selftest_ch1"] = bool(reg_144 & (1 << 4)) 
                        data["afci_selftest_ch2"] = bool(reg_144 & (1 << 5))
                        data["afci_selftest_ch3"] = bool(reg_144 & (1 << 6))
                        data["afci_selftest_ch4"] = bool(reg_144 & (1 << 7))
                        
                        data["afci_arc_ch1"] = decoder.decode_16bit_uint()
                        data["afci_arc_ch2"] = decoder.decode_16bit_uint()
                        data["afci_arc_ch3"] = decoder.decode_16bit_uint()
                        data["afci_arc_ch4"] = decoder.decode_16bit_uint()
                        data["afci_max_arc_ch1"] = decoder.decode_16bit_uint()
                        data["afci_max_arc_ch2"] = decoder.decode_16bit_uint()
                        data["afci_max_arc_ch3"] = decoder.decode_16bit_uint()
                        data["afci_max_arc_ch4"] = decoder.decode_16bit_uint()
                    else:
                        _LOGGER.warning("Modbus read error on input registers 120-152")

                    # =================================================================================
                    # Read Holding Registers (Function Code 0x03)
                    # =================================================================================
                    
                    # --- Block 1: Registers 9-24 ---
                    result = client.read_holding_registers(9, count=16, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        info_ver_reg9 = decoder.decode_16bit_uint()
                        data["info_com_version"] = info_ver_reg9 >> 8
                        info_ver_reg10 = decoder.decode_16bit_uint()
                        data["info_controller_version"] = info_ver_reg10 & 0xFF
                        decoder.skip_registers(1)
                        
                        time_reg12 = decoder.decode_16bit_uint()
                        time_reg13 = decoder.decode_16bit_uint()
                        time_reg14 = decoder.decode_16bit_uint()
                        
                        year = 2000 + (time_reg12 & 0xFF)
                        month = time_reg12 >> 8
                        day = time_reg13 & 0xFF
                        hour = time_reg13 >> 8
                        minute = time_reg14 & 0xFF
                        second = time_reg14 >> 8
                        try:
                            inverter_time = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
                            now = dt_util.utcnow()
                            time_difference = abs(now - inverter_time)
                            data["inverter_time_accurate"] = time_difference <= timedelta(seconds=30)
                        except ValueError:
                            _LOGGER.warning("Invalid date components received from inverter")
                            data["inverter_time_accurate"] = False
                        
                        data["setting_address_communication"] = decoder.decode_16bit_uint()
                        data["setting_language"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(3)
                        data["setting_pv_input_model"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(1)
                        data["setting_voltage_pv_start"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_time_grid_connection_wait"] = decoder.decode_16bit_uint()
                        data["setting_time_reconnection_wait"] = decoder.decode_16bit_uint()
                    else:
                        _LOGGER.warning("Modbus read error on holding registers 9-24")

                    # --- Block 2: Registers 64-119 ---
                    result = client.read_holding_registers(64, count=56, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_percent_charge_power"] = decoder.decode_16bit_uint()
                        data["setting_percent_discharge_power"] = decoder.decode_16bit_uint()
                        data["setting_percent_ac_charge_power"] = decoder.decode_16bit_uint()
                        data["setting_limit_soc_ac_charge"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(22)
                        data["setting_voltage_inverter"] = decoder.decode_16bit_uint()
                        data["setting_frequency_inverter"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(7)
                        data["setting_voltage_charge_ref"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_discharge_cutoff"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_current_charge"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_current_discharge"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_max_backflow_power"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(1)
                        data["setting_eod_soc"] = decoder.decode_16bit_uint()
                        data["setting_temp_low_limit_discharge"] = decoder.decode_16bit_int() / 10.0
                        data["setting_temp_high_limit_discharge"] = decoder.decode_16bit_int() / 10.0
                        data["setting_temp_low_limit_charge"] = decoder.decode_16bit_int() / 10.0
                        data["setting_temp_high_limit_charge"] = decoder.decode_16bit_int() / 10.0
                        decoder.skip_registers(2)
                        data["setting_system_type"] = decoder.decode_16bit_uint()
                        data["setting_composed_phase"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(2)
                        data["setting_ptouser_start_discharge"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(1)
                        data["setting_voltage_start_derating"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_power_offset_wct"] = decoder.decode_16bit_int()
                    else:
                        _LOGGER.warning("Modbus read error on holding registers 64-119")

                    # --- Block 3: Registers 125, 144-151, 158-169, 176-177, 194-198 ---
                    result = client.read_holding_registers(125, count=1, **self._kwargs)
                    if not result.isError(): 
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_soc_low_limit_inverter_discharge"] = decoder.decode_16bit_uint()
                    
                    result = client.read_holding_registers(144, count=8, **self._kwargs)
                    if not result.isError():
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_voltage_float_charge"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_output_priority_config"] = decoder.decode_16bit_uint()
                        data["setting_line_mode"] = decoder.decode_16bit_uint()
                        data["setting_battery_capacity"] = decoder.decode_16bit_uint()
                        data["setting_battery_nominal_voltage"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_equalization"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_equalization_interval"] = decoder.decode_16bit_uint()
                        data["setting_equalization_time"] = decoder.decode_16bit_uint()
                    
                    result = client.read_holding_registers(158, count=12, **self._kwargs)
                    if not result.isError():
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_voltage_ac_charge_start"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_ac_charge_end"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_soc_ac_charge_start"] = decoder.decode_16bit_uint()
                        data["setting_soc_ac_charge_end"] = decoder.decode_16bit_uint()
                        data["setting_voltage_battery_low"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_battery_low_back"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_soc_battery_low"] = decoder.decode_16bit_uint()
                        data["setting_soc_battery_low_back"] = decoder.decode_16bit_uint()
                        data["setting_voltage_battery_low_to_utility"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_soc_battery_low_to_utility"] = decoder.decode_16bit_uint()
                        data["setting_current_ac_charge_battery"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_ongrid_eod"] = decoder.decode_16bit_uint() / 10.0
                    
                    result = client.read_holding_registers(176, count=2, **self._kwargs)
                    if not result.isError():
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_power_max_grid_input"] = decoder.decode_16bit_uint()
                        data["setting_power_gen_rated"] = decoder.decode_16bit_uint()
                    
                    result = client.read_holding_registers(194, count=5, **self._kwargs)
                    if not result.isError():
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_voltage_gen_charge_start"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_gen_charge_end"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_soc_gen_charge_start"] = decoder.decode_16bit_uint()
                        data["setting_soc_gen_charge_end"] = decoder.decode_16bit_uint()
                        data["setting_current_max_gen_charge_battery"] = decoder.decode_16bit_uint() / 10.0

            except IndexError:
                _LOGGER.warning("IndexError during Modbus decoding. Inverter response may be shorter than expected.")
            except ConnectionException as ex:
                _LOGGER.error(f"Modbus connection failed during update: {ex}")
                return self.data # Return last known data
            except Exception as e:
                _LOGGER.error(f"An unexpected error occurred during Modbus update: {e}")
                return self.data # Return last known data


        # --- Final Calculations ---
        if updated:
            data['power_pv_total'] = data.get('power_pv1', 0) + data.get('power_pv2', 0) + data.get('power_pv3', 0)
            
            pv_voltages = [v for v in [data.get('voltage_pv1', 0), data.get('voltage_pv2', 0), data.get('voltage_pv3', 0)] if v > 25]
            
            if pv_voltages:
                data['voltage_pv_average'] = sum(pv_voltages) / len(pv_voltages)
            else:
                data['voltage_pv_average'] = 0
                
            data['power_battery_total'] = data.get('power_battery_charge', 0) - data.get('power_battery_discharge', 0)
            data['energy_daily_pv_total'] = data.get('energy_daily_pv1', 0) + data.get('energy_daily_pv2', 0) + data.get('energy_daily_pv3', 0)
            data['energy_cumulative_pv'] = data.get('energy_cumulative_pv1', 0) + data.get('energy_cumulative_pv2', 0) + data.get('energy_cumulative_pv3', 0)
            
            data['power_grid_total'] = data.get('power_grid_import', 0) - data.get('power_grid_export', 0)

            self.data = data
            return self.data
        
        _LOGGER.warning("Modbus update failed to read any new data, returning last known values.")
        return self.data

    def translate_bitmask_to_messages(self, code: int, message_map: dict) -> str:
        """Translate a bitmask code into a comma-separated string of messages."""
        if not code:
            return "No Faults"

        messages = [
            message for bit, message in message_map.items() if (code & bit)
        ]
        
        if not messages:
            return f"Unknown Code: {hex(code)}"

        return ", ".join(messages)