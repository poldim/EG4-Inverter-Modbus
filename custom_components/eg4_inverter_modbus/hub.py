"""EG4 Modbus Hub"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import inspect
import logging
import queue
import struct
import threading
import time
from typing import Optional

from homeassistant.core import CALLBACK_TYPE, callback, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

import pymodbus
from pymodbus import __version__ as pymodbus_version
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

class SafeModbusTcpClient(ModbusTcpClient):
    """A wrapper around ModbusTcpClient that closes the socket on any error."""
    def __enter__(self):
        if not self.is_socket_open():
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def read_input_registers(self, *args, **kwargs):
        time.sleep(0.05)
        try:
            res = super().read_input_registers(*args, **kwargs)
        except Exception as e:
            self.close()
            raise ConnectionException(f"Modbus input read exception: {e}") from e
        if res is None or res.isError():
            self.close()
            raise ConnectionException(f"Modbus input read error: {res}")
        return res

    def read_holding_registers(self, *args, **kwargs):
        time.sleep(0.05)
        try:
            res = super().read_holding_registers(*args, **kwargs)
        except Exception as e:
            self.close()
            raise ConnectionException(f"Modbus holding read exception: {e}") from e
        if res is None or res.isError():
            self.close()
            raise ConnectionException(f"Modbus holding read error: {res}")
        return res

    def write_register(self, *args, **kwargs):
        time.sleep(0.05)
        try:
            res = super().write_register(*args, **kwargs)
        except Exception as e:
            self.close()
            raise ConnectionException(f"Modbus write exception: {e}") from e
        if res is None or res.isError():
            self.close()
            raise ConnectionException(f"Modbus write error: {res}")
        return res

    def write_registers(self, *args, **kwargs):
        time.sleep(0.05)
        try:
            res = super().write_registers(*args, **kwargs)
        except Exception as e:
            self.close()
            raise ConnectionException(f"Modbus write exception: {e}") from e
        if res is None or res.isError():
            self.close()
            raise ConnectionException(f"Modbus write error: {res}")
        return res

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


@dataclass
class _WriteRequest:
    """A pending write request queued for processing on the next poll cycle."""
    address: int
    value: int
    done: threading.Event = field(default_factory=threading.Event)
    result: bool = False


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
        self._client = SafeModbusTcpClient(host=host, port=port, timeout=5)
        self._device_id = slave if slave else 1
        self._lock = threading.Lock()
        self._write_queue: queue.SimpleQueue[_WriteRequest] = queue.SimpleQueue()
        self.data: dict = {}
        self.battery_count: int = 0
        self._consecutive_rejects: dict[str, int] = {}
        
        self._pyversion = parse_version(pymodbus_version)

        possible_kwarg_names = ("slave", "unit", "device_id")

        def _detect_kwarg(method_name: str) -> Optional[str]:
            # Inspect the base class ModbusTcpClient to bypass the SafeModbusTcpClient wrapper
            method = getattr(ModbusTcpClient, method_name, None)
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

    def get_device_info(self, key: str, entity_category) -> dict:
        """Return the device info for a given entity key and category."""
        import re
        from homeassistant.helpers.entity import EntityCategory
        from homeassistant.helpers import device_registry as dr
        from .const import DOMAIN, ATTR_MANUFACTURER

        via_device_id = None
        if hasattr(self, "hass") and self.hass is not None:
            try:
                dev_reg = dr.async_get(self.hass)
                if parent_dev := dev_reg.async_get_device(identifiers={(DOMAIN, self.name)}):
                    via_device_id = parent_dev.id
            except Exception:
                pass
        
        # 1. Check if battery
        battery_match = re.match(r"^battery(\d+)_", key)
        if battery_match:
            battery_num = int(battery_match.group(1))
            info = {
                "identifiers": {(DOMAIN, f"{self.name}_battery_{battery_num}")},
                "name": f"{self.name} Battery {battery_num}",
                "manufacturer": ATTR_MANUFACTURER,
                "model": "EG4 Battery",
            }
            if via_device_id:
                info["via_device_id"] = via_device_id
            return info
        
        # 2. Check if Settings/Diagnostic
        if key.startswith("setting_") or entity_category in (EntityCategory.CONFIG, EntityCategory.DIAGNOSTIC):
            info = {
                "identifiers": {(DOMAIN, f"{self.name}_settings")},
                "name": f"{self.name} Inverter Settings",
                "manufacturer": ATTR_MANUFACTURER,
                "model": "EG4 Inverter Settings",
            }
            if via_device_id:
                info["via_device_id"] = via_device_id
            return info
            
        # 3. Default to main inverter device
        return {
            "identifiers": {(DOMAIN, self.name)},
            "name": self.name,
            "manufacturer": ATTR_MANUFACTURER,
            "model": "EG4 Inverter",
        }

    @callback
    def async_remove_listener(self, update_callback: CALLBACK_TYPE) -> None:
        """Remove data update listener."""
        super().async_remove_listener(update_callback)
        if not self._listeners:
            self.close()

    def close(self) -> None:
        """Disconnect client."""
        # Signal any pending writes that they will not be processed
        try:
            while True:
                req = self._write_queue.get_nowait()
                req.result = False
                req.done.set()
        except queue.Empty:
            pass
        with self._lock:
            if self._client.is_socket_open():
                self._client.close()

    def write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        value = value & 0xFFFF
        if self._kwargs is None:
            _LOGGER.error("Cannot write register: integration has not successfully polled yet. Please wait.")
            return False

        req = _WriteRequest(address=address, value=value)
        self._write_queue.put(req)
        _LOGGER.debug(f"Write queued for register {address} = {value}. Triggering immediate refresh.")

        # Trigger immediate poll cycle on event loop to process the write queue right away
        def _request_refresh() -> None:
            self.hass.async_create_task(self.async_request_refresh())

        self.hass.loop.call_soon_threadsafe(_request_refresh)

        # Block the executor thread until the poll loop processes this write.
        # Timeout of 60 s guards against HA shutdown before the next poll.
        completed = req.done.wait(timeout=60)
        if not completed:
            _LOGGER.error(f"Timed out waiting for write to register {address} to be processed.")
            return False

        if not req.result:
            _LOGGER.error(f"Write to register {address} failed during poll cycle.")
        return req.result

    def discover_batteries(self) -> None:
        """Scan Modbus registers to detect the number of connected batteries."""
        self.battery_count = 0
        from .const import MAX_BATTERIES
        with self._lock:
            try:
                with self._client as client:
                    if not client.is_socket_open():
                        client.connect()
                    if not client.is_socket_open():
                        _LOGGER.warning("Could not connect to inverter for battery discovery.")
                        return

                    for i in range(MAX_BATTERIES):
                        address = 5000 + (30 * i)
                        result = client.read_input_registers(address, count=30, **self._kwargs)
                        if result.isError():
                            break
                        
                        # Verify the valid marker at index 2 (offset 2) is present or capacity exists
                        if len(result.registers) > 3 and result.registers[2] == 0xC002:
                            self.battery_count += 1
                        else:
                            # Also allow if it doesn't have 0xC002 but has a valid capacity at index 3
                            if len(result.registers) > 3 and result.registers[3] > 0 and result.registers[3] < 2000:
                                self.battery_count += 1
                            else:
                                break
                            
                    _LOGGER.info(f"Discovered {self.battery_count} batteries.")
            except Exception as e:
                _LOGGER.error(f"Error during battery discovery: {e}")

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
                    # Drain Write Queue (process any pending writes BEFORE reading)
                    # =================================================================================
                    while True:
                        try:
                            req = self._write_queue.get_nowait()
                        except queue.Empty:
                            break
                        try:
                            _LOGGER.debug(f"Processing queued write: register {req.address} = {req.value}")
                            res = client.write_register(address=req.address, value=req.value, **self._kwargs)
                            req.result = not res.isError()
                            if res.isError():
                                _LOGGER.error(f"Queued write to register {req.address} failed: {res}")
                        except Exception as e:
                            req.result = False
                            _LOGGER.error(f"Queued write to register {req.address} raised exception: {e}")
                        finally:
                            req.done.set()

                    # =================================================================================
                    # Read Input Registers (Function Code 0x04)
                    # =================================================================================
                    
                    # --- Battery Blocks ---
                    for i in range(self.battery_count):
                        address = 5000 + (30 * i)
                        result = client.read_input_registers(address, count=30, **self._kwargs)
                        if not result.isError():
                            updated = True
                            decoder = CustomPayloadDecoder(result.registers)
                            prefix = f"battery{i+1:02d}"
                            
                            try:
                                decoder.skip_registers(3) # Skip 0, 1, 2
                                data[f"{prefix}_capacity_pack"] = decoder.decode_16bit_uint()
                                data[f"{prefix}_capacity_system"] = decoder.decode_16bit_uint()
                                data[f"{prefix}_current_max_charge"] = decoder.decode_16bit_uint() / 10.0
                                data[f"{prefix}_current_max_discharge"] = decoder.decode_16bit_uint() / 10.0
                                decoder.skip_registers(1) # Discharge Voltage Ref / Do Not Use
                                data[f"{prefix}_voltage"] = decoder.decode_16bit_uint() / 100.0
                                data[f"{prefix}_current"] = decoder.decode_16bit_int() / 10.0
                                
                                soh_soc = decoder.decode_16bit_uint()
                                data[f"{prefix}_soh"] = soh_soc >> 8
                                data[f"{prefix}_soc"] = soh_soc & 0xFF
                                
                                data[f"{prefix}_cycle_count"] = decoder.decode_16bit_uint()
                                data[f"{prefix}_max_cell_temp"] = decoder.decode_16bit_uint() / 10.0
                                data[f"{prefix}_min_cell_temp"] = decoder.decode_16bit_uint() / 10.0
                                data[f"{prefix}_max_cell_voltage"] = decoder.decode_16bit_uint() / 1000.0
                                data[f"{prefix}_min_cell_voltage"] = decoder.decode_16bit_uint() / 1000.0
                                
                                temp_cells_raw = decoder.decode_16bit_uint()
                                data[f"{prefix}_cell_temp_min"] = f"Cell {temp_cells_raw >> 8}"
                                data[f"{prefix}_cell_temp_max"] = f"Cell {temp_cells_raw & 0xFF}"
                                
                                voltage_cells_raw = decoder.decode_16bit_uint()
                                data[f"{prefix}_cell_voltage_min"] = f"Cell {voltage_cells_raw >> 8}"
                                data[f"{prefix}_cell_voltage_max"] = f"Cell {voltage_cells_raw & 0xFF}"
                                
                                firmware_raw = decoder.decode_16bit_uint()
                                data[f"{prefix}_firmware"] = f"{firmware_raw >> 8}.{firmware_raw & 0xFF}"
                                
                                serial_chars = []
                                for _ in range(7):
                                    val = decoder.decode_16bit_uint()
                                    c1 = val & 0xFF
                                    c2 = val >> 8
                                    if c1: serial_chars.append(chr(c1))
                                    if c2: serial_chars.append(chr(c2))
                                data[f"{prefix}_serial_id"] = "".join(serial_chars).rstrip('\x00')
                                
                                # Calculated values
                                data[f"{prefix}_remaining_capacity"] = data[f"{prefix}_capacity_pack"] * (data[f"{prefix}_soc"] / 100.0)
                                data[f"{prefix}_cell_voltage_delta"] = round(data[f"{prefix}_max_cell_voltage"] - data[f"{prefix}_min_cell_voltage"], 3)
                                
                                temp_delta_c = data[f"{prefix}_max_cell_temp"] - data[f"{prefix}_min_cell_temp"]
                                if self.hass.config.units.temperature_unit == "°C":
                                    data[f"{prefix}_cell_temp_delta"] = round(temp_delta_c, 1)
                                else:
                                    data[f"{prefix}_cell_temp_delta"] = round(temp_delta_c * 1.8, 1)
                                    
                                data[f"{prefix}_real_power"] = round(data[f"{prefix}_voltage"] * data[f"{prefix}_current"], 1)
                                if data[f"{prefix}_capacity_pack"] > 0:
                                    data[f"{prefix}_current_flow_rate"] = round((data[f"{prefix}_current"] / data[f"{prefix}_capacity_pack"]) * 100.0, 2)
                                else:
                                    data[f"{prefix}_current_flow_rate"] = 0.0
                                
                                decoder.skip_registers(4) # Skip remaining registers (5026-5029) to reach the end of 30 registers block
                            except IndexError:
                                _LOGGER.warning(f"IndexError decoding battery {i+1} block. Inverter response shorter than expected.")

                    # --- Block 1: Registers 0-39 ---
                    result = client.read_input_registers(0, count=40, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["inverter_mode"] = INVERTER_STATUS_CODES.get(decoder.decode_16bit_uint(), "Unknown")
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
                        def clean_ac_voltage(v: float) -> float | None:
                            return v if v < 400.0 else None
                            
                        data["voltage_grid_l1l2"] = clean_ac_voltage(decoder.decode_16bit_uint() / 10.0)
                        data["voltage_grid_l2l3"] = clean_ac_voltage(decoder.decode_16bit_uint() / 10.0)
                        data["voltage_grid_l3l1"] = clean_ac_voltage(decoder.decode_16bit_uint() / 10.0)
                        
                        fac_pinv_reg = decoder.decode_16bit_uint()
                        data["frequency_grid"] = (fac_pinv_reg) / 100.0
                        data["power_inverter_output"] = decoder.decode_16bit_uint()
                        data["power_ac_charge"] = decoder.decode_16bit_uint()
                        data["current_inverter_rms"] = decoder.decode_16bit_uint() / 100.0
                        data["power_factor_inverter"] = decoder.decode_16bit_uint() / 1000.0
                        data["voltage_inverter_l1l2"] = clean_ac_voltage(decoder.decode_16bit_uint() / 10.0)
                        data["voltage_inverter_l2l3"] = clean_ac_voltage(decoder.decode_16bit_uint() / 10.0)
                        data["voltage_inverter_l3l1"] = clean_ac_voltage(decoder.decode_16bit_uint() / 10.0)
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
                        calculated_on_time = (current_time - timedelta(seconds=time_running_total_seconds)).replace(microsecond=0)
                        prev_on_time = self.data.get("inverter_on_time")
                        if (
                            isinstance(prev_on_time, datetime)
                            and prev_on_time.tzinfo is not None
                            and abs((calculated_on_time - prev_on_time).total_seconds()) <= 60
                        ):
                            data["inverter_on_time"] = prev_on_time
                        else:
                            data["inverter_on_time"] = calculated_on_time
                        data["inverter_uptime_days"] = round(time_running_total_seconds / 86400, 1)
                        
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
                        def get_probe_temp(val: float) -> float | None:
                            return val if val != 0.0 else None

                        data["temperature_t1"] = get_probe_temp(decoder.decode_16bit_int() / 10.0)
                        data["temperature_t2"] = get_probe_temp(decoder.decode_16bit_int() / 10.0)
                        data["temperature_t3"] = get_probe_temp(decoder.decode_16bit_int() / 10.0)
                        data["temperature_t4"] = get_probe_temp(decoder.decode_16bit_int() / 10.0)
                        data["temperature_t5"] = get_probe_temp(decoder.decode_16bit_int() / 10.0)
                        parallel_reg = decoder.decode_16bit_uint()
                        data["parallel_master_slave"] = parallel_reg & 0x03
                        data["parallel_phase"] = (parallel_reg >> 2) & 0x03
                        data["parallel_number"] = parallel_reg >> 8
                        data["power_load_on_grid"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(4)
                        
                    else:
                        _LOGGER.warning("Modbus read error on input registers 80-119")

                    # --- Block 4: Registers 120-159 ---
                    result = client.read_input_registers(120, count=40, **self._kwargs)
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
                        data["afci_current_ch1"] = decoder.decode_16bit_uint() / 10.0
                        data["afci_current_ch2"] = decoder.decode_16bit_uint() / 10.0
                        data["afci_current_ch3"] = decoder.decode_16bit_uint() / 10.0
                        data["afci_current_ch4"] = decoder.decode_16bit_uint() / 10.0
                        
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
                        data["power_inverter_ac_coupled"] = decoder.decode_16bit_uint()
                    else:
                        _LOGGER.warning("Modbus read error on input registers 120-159")

                    # --- Block 5: Registers 170-193 ---
                    result = client.read_input_registers(170, count=24, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["power_load"] = decoder.decode_16bit_uint()
                        data["energy_daily_load"] = decoder.decode_16bit_uint() / 10.0
                        data["energy_cumulative_load"] = decoder.decode_32bit_uint() / 10.0
                        decoder.skip_registers(6)
                        data["power_inverter_on_grid_l2"] = decoder.decode_16bit_uint()
                        data["power_inverter_on_grid_l3"] = decoder.decode_16bit_uint()
                        data["power_charging_rectification_l2"] = decoder.decode_16bit_uint()
                        data["power_charging_rectification_l3"] = decoder.decode_16bit_uint()
                        data["power_grid_output_load_terminal_l2"] = decoder.decode_16bit_uint()
                        data["power_grid_output_load_terminal_l3"] = decoder.decode_16bit_uint()
                        data["power_grid_power_supply_l2"] = decoder.decode_16bit_uint()
                        data["power_grid_power_supply_l3"] = decoder.decode_16bit_uint()
                        data["power_gen_terminal_l2"] = decoder.decode_16bit_uint()
                        data["power_gen_terminal_l3"] = decoder.decode_16bit_uint()
                        data["current_inverter_rms_l2"] = decoder.decode_16bit_uint() / 100.0
                        data["current_inverter_rms_l3"] = decoder.decode_16bit_uint() / 100.0
                        data["power_factor_inverter_l2"] = decoder.decode_16bit_uint() / 1000.0
                        data["power_factor_inverter_l3"] = decoder.decode_16bit_uint() / 1000.0
                    else:
                        _LOGGER.warning("Modbus read error on input registers 170-193")

                    # =================================================================================
                    # Read Holding Registers (Function Code 0x03)
                    # =================================================================================
                    
                    # --- Block 1: Registers 9-24 ---
                    result = client.read_holding_registers(9, count=16, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        info_ver_reg9 = decoder.decode_16bit_uint()
                        data["hardware_com_version"] = info_ver_reg9 >> 8
                        info_ver_reg10 = decoder.decode_16bit_uint()
                        data["hardware_controller_version"] = info_ver_reg10 & 0xFF
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
                            # Inverter time is local time, HA we use local time (naive)
                            inverter_time = datetime(year, month, day, hour, minute, second)
                            now = dt_util.now().replace(tzinfo=None)
                            time_difference = abs(now - inverter_time)
                            data["inverter_time_accurate"] = time_difference <= timedelta(seconds=100)
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
                        data["setting_time_grid_reconnection_wait"] = decoder.decode_16bit_uint()
                    else:
                        _LOGGER.warning("Modbus read error on holding registers 9-24")

                    result = client.read_holding_registers(21, count=1, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        reg21 = decoder.decode_16bit_uint()
                        data["setting_func_en_eps"] = (reg21 >> 0) & 1
                        data["setting_func_en_ovf_load_derate"] = (reg21 >> 1) & 1
                        data["setting_func_en_drms"] = (reg21 >> 2) & 1
                        data["setting_func_en_lvrt"] = (reg21 >> 3) & 1
                        data["setting_func_en_anti_island"] = (reg21 >> 4) & 1
                        data["setting_func_en_neutral_detect"] = (reg21 >> 5) & 1
                        data["setting_func_en_grid_on_power_ss"] = (reg21 >> 6) & 1
                        data["setting_func_en_ac_charge"] = (reg21 >> 7) & 1
                        data["setting_func_en_sw_seamlessly"] = (reg21 >> 8) & 1
                        data["setting_func_en_set_to_standby"] = (reg21 >> 9) & 1
                        data["setting_func_en_forced_dischg"] = (reg21 >> 10) & 1
                        data["setting_func_en_forced_chg"] = (reg21 >> 11) & 1
                        data["setting_func_en_iso"] = (reg21 >> 12) & 1
                        data["setting_func_en_gfci"] = (reg21 >> 13) & 1
                        data["setting_func_en_dci"] = (reg21 >> 14) & 1
                        data["setting_func_en_feed_in_grid"] = (reg21 >> 15) & 1
                    else:
                        _LOGGER.warning("Modbus read error on holding register 21")

                    # --- Register 59: Reactive Power Command Type ---
                    result = client.read_holding_registers(59, count=1, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_reactive_power_cmd_type"] = decoder.decode_16bit_uint()
                    else:
                        _LOGGER.warning("Modbus read error on holding register 59")

                    # --- Block 2: Registers 64-119 ---
                    result = client.read_holding_registers(64, count=56, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_percent_charge_power"] = decoder.decode_16bit_uint()
                        data["setting_percent_discharge_power"] = decoder.decode_16bit_uint()
                        val_66 = decoder.decode_16bit_uint()
                        data["setting_ac_charge_rate"] = val_66 / 10.0
                        data["setting_percent_ac_charge_power"] = val_66
                        data["setting_limit_soc_ac_charge"] = decoder.decode_16bit_uint()
                        for slot in ("t1_start", "t1_end", "t2_start", "t2_end", "t3_start", "t3_end"):
                            val = decoder.decode_16bit_uint()
                            data[f"setting_ac_charge_{slot}_hour"] = val & 0xFF
                            data[f"setting_ac_charge_{slot}_minute"] = (val >> 8) & 0xFF
                        decoder.skip_registers(16)
                        data["setting_voltage_inverter"] = decoder.decode_16bit_uint()
                        data["setting_frequency_inverter"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(7)
                        data["setting_voltage_charge_ref"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_voltage_discharge_cutoff"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_current_charge"] = decoder.decode_16bit_uint()
                        data["setting_current_discharge"] = decoder.decode_16bit_uint()
                        data["setting_max_backflow_power"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(1)
                        data["setting_eod_soc"] = decoder.decode_16bit_uint()
                        data["setting_temp_low_limit_discharge"] = decoder.decode_16bit_int() / 10.0
                        data["setting_temp_high_limit_discharge"] = decoder.decode_16bit_int() / 10.0
                        data["setting_temp_low_limit_charge"] = decoder.decode_16bit_int() / 10.0
                        data["setting_temp_high_limit_charge"] = decoder.decode_16bit_int() / 10.0
                        reg110 = decoder.decode_16bit_uint()
                        data["setting_functionen1_ubpvgridoffen"] = (reg110 >> 0) & 1
                        data["setting_functionen1_ubfastzeroexport"] = (reg110 >> 1) & 1
                        data["setting_functionen1_ubmicrogriden"] = (reg110 >> 2) & 1
                        data["setting_functionen1_ubbatshared"] = (reg110 >> 3) & 1
                        data["setting_functionen1_ubchglasten"] = (reg110 >> 4) & 1
                        data["setting_functionen1_ctsampleratio"] = (reg110 >> 5) & 3
                        data["setting_functionen1_buzzeren"] = (reg110 >> 7) & 1
                        data["setting_functionen1_pvctsampletype"] = (reg110 >> 8) & 3
                        data["setting_functionen1_takeloadtogether"] = (reg110 >> 10) & 1
                        data["setting_functionen1_ongridworkingmode"] = (reg110 >> 11) & 1
                        data["setting_functionen1_pvctsampleratio"] = (reg110 >> 12) & 3
                        data["setting_functionen1_greenmodeen"] = (reg110 >> 14) & 1
                        data["setting_functionen1_ecomodeen"] = (reg110 >> 15) & 1
                        decoder.skip_registers(1)
                        data["setting_system_type"] = decoder.decode_16bit_uint()
                        data["setting_composed_phase"] = decoder.decode_16bit_uint() & 0xFF
                        decoder.skip_registers(2)
                        data["setting_ptouser_start_discharge"] = decoder.decode_16bit_uint()
                        decoder.skip_registers(1)
                        data["setting_voltage_start_derating"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_power_offset_wct"] = decoder.decode_16bit_int() / 10.0
                    else:
                        _LOGGER.warning("Modbus read error on holding registers 64-119")

                    # --- Block 3: Registers 120, 125, 144-151, 158-169, 176-177, 194-198 ---
                    result = client.read_holding_registers(120, count=1, **self._kwargs)
                    if not result.isError():
                        updated = True
                        reg120 = result.registers[0]
                        data["setting_half_hour_ac_chr_start_en"] = reg120 & 0x01
                        data["setting_ac_charge_type"] = (reg120 >> 1) & 0x07
                        data["setting_discharge_control_type"] = (reg120 >> 4) & 0x03
                        data["setting_ongrid_eod_type"] = (reg120 >> 6) & 0x01
                        data["setting_generator_charge_type"] = (reg120 >> 7) & 0x01
                        data["setting_separate_zero_export_en"] = (reg120 >> 8) & 0x01
                    else:
                        _LOGGER.warning("Modbus read error on holding register 120")

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
                        val_147 = decoder.decode_16bit_uint()
                        data["setting_battery_capacity_unmatched_override"] = val_147
                        data["setting_battery_capacity"] = val_147
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


                    # --- Block 4: Registers 126-131 (Optimal Time) ---
                    result = client.read_holding_registers(126, count=6, **self._kwargs)
                    if not result.isError():
                        updated = True
                        regs = result.registers
                        # 126 (Times 00-07)
                        data["setting_hourly_charge_discharge_time_0"] = (regs[0] >> 0) & 3
                        data["setting_hourly_charge_discharge_time_1"] = (regs[0] >> 2) & 3
                        data["setting_hourly_charge_discharge_time_2"] = (regs[0] >> 4) & 3
                        data["setting_hourly_charge_discharge_time_3"] = (regs[0] >> 6) & 3
                        data["setting_hourly_charge_discharge_time_4"] = (regs[0] >> 8) & 3
                        data["setting_hourly_charge_discharge_time_5"] = (regs[0] >> 10) & 3
                        data["setting_hourly_charge_discharge_time_6"] = (regs[0] >> 12) & 3
                        data["setting_hourly_charge_discharge_time_7"] = (regs[0] >> 14) & 3
                        # 127 (Times 08-15)
                        data["setting_hourly_charge_discharge_time_8"] = (regs[1] >> 0) & 3
                        data["setting_hourly_charge_discharge_time_9"] = (regs[1] >> 2) & 3
                        data["setting_hourly_charge_discharge_time_10"] = (regs[1] >> 4) & 3
                        data["setting_hourly_charge_discharge_time_11"] = (regs[1] >> 6) & 3
                        data["setting_hourly_charge_discharge_time_12"] = (regs[1] >> 8) & 3
                        data["setting_hourly_charge_discharge_time_13"] = (regs[1] >> 10) & 3
                        data["setting_hourly_charge_discharge_time_14"] = (regs[1] >> 12) & 3
                        data["setting_hourly_charge_discharge_time_15"] = (regs[1] >> 14) & 3
                        # 128 (Times 16-23)
                        data["setting_hourly_charge_discharge_time_16"] = (regs[2] >> 0) & 3
                        data["setting_hourly_charge_discharge_time_17"] = (regs[2] >> 2) & 3
                        data["setting_hourly_charge_discharge_time_18"] = (regs[2] >> 4) & 3
                        data["setting_hourly_charge_discharge_time_19"] = (regs[2] >> 6) & 3
                        data["setting_hourly_charge_discharge_time_20"] = (regs[2] >> 8) & 3
                        data["setting_hourly_charge_discharge_time_21"] = (regs[2] >> 10) & 3
                        data["setting_hourly_charge_discharge_time_22"] = (regs[2] >> 12) & 3
                        data["setting_hourly_charge_discharge_time_23"] = (regs[2] >> 14) & 3
                        # 129 (Times 24-31)
                        data["setting_hourly_charge_discharge_time_24"] = (regs[3] >> 0) & 3
                        data["setting_hourly_charge_discharge_time_25"] = (regs[3] >> 2) & 3
                        data["setting_hourly_charge_discharge_time_26"] = (regs[3] >> 4) & 3
                        data["setting_hourly_charge_discharge_time_27"] = (regs[3] >> 6) & 3
                        data["setting_hourly_charge_discharge_time_28"] = (regs[3] >> 8) & 3
                        data["setting_hourly_charge_discharge_time_29"] = (regs[3] >> 10) & 3
                        data["setting_hourly_charge_discharge_time_30"] = (regs[3] >> 12) & 3
                        data["setting_hourly_charge_discharge_time_31"] = (regs[3] >> 14) & 3
                        # 130 (Times 32-39)
                        data["setting_hourly_charge_discharge_time_32"] = (regs[4] >> 0) & 3
                        data["setting_hourly_charge_discharge_time_33"] = (regs[4] >> 2) & 3
                        data["setting_hourly_charge_discharge_time_34"] = (regs[4] >> 4) & 3
                        data["setting_hourly_charge_discharge_time_35"] = (regs[4] >> 6) & 3
                        data["setting_hourly_charge_discharge_time_36"] = (regs[4] >> 8) & 3
                        data["setting_hourly_charge_discharge_time_37"] = (regs[4] >> 10) & 3
                        data["setting_hourly_charge_discharge_time_38"] = (regs[4] >> 12) & 3
                        data["setting_hourly_charge_discharge_time_39"] = (regs[4] >> 14) & 3
                        # 131 (Times 40-47)
                        data["setting_hourly_charge_discharge_time_40"] = (regs[5] >> 0) & 3
                        data["setting_hourly_charge_discharge_time_41"] = (regs[5] >> 2) & 3
                        data["setting_hourly_charge_discharge_time_42"] = (regs[5] >> 4) & 3
                        data["setting_hourly_charge_discharge_time_43"] = (regs[5] >> 6) & 3
                        data["setting_hourly_charge_discharge_time_44"] = (regs[5] >> 8) & 3
                        data["setting_hourly_charge_discharge_time_45"] = (regs[5] >> 10) & 3
                        data["setting_hourly_charge_discharge_time_46"] = (regs[5] >> 12) & 3
                        data["setting_hourly_charge_discharge_time_47"] = (regs[5] >> 14) & 3

                    # --- Block 5: Register 179 (Function En 2) ---
                    result = client.read_holding_registers(179, count=1, **self._kwargs)
                    if not result.isError():
                        updated = True
                        val = result.registers[0]
                        data["setting_ufunctionen2_grid_peak_shaving"] = (val >> 7) & 1
                        data["setting_ufunctionen2_gen_peak_shaving"] = (val >> 8) & 1
                        data["setting_ufunctionen2_bat_chg_control"] = (val >> 9) & 1
                        data["setting_ufunctionen2_bat_dischg_control"] = (val >> 10) & 1
                        data["setting_ufunctionen2_ac_coupling"] = (val >> 11) & 1
                        data["setting_ufunctionen2_pv_arc_en"] = (val >> 12) & 1
                        data["setting_ufunctionen2_smart_load_en"] = (val >> 13) & 1
                        data["setting_ufunctionen2_rsd_disable"] = (val >> 14) & 1
                        data["setting_ufunctionen2_ongrid_always_on"] = (val >> 15) & 1

                    # --- Block 6: Registers 199-228 ---
                    result = client.read_holding_registers(199, count=30, **self._kwargs)
                    if not result.isError():
                        updated = True
                        decoder = CustomPayloadDecoder(result.registers)
                        data["setting_over_temp_derate_point"] = decoder.decode_16bit_int() / 10.0
                        decoder.skip_registers(1) # 200
                        data["setting_chg_first_end_volt"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_force_dischg_end_volt"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_grid_regulation"] = decoder.decode_16bit_uint()
                        data["setting_lead_capacity"] = decoder.decode_16bit_uint()
                        data["setting_grid_type"] = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_power"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_peak_shaving_a_soc"] = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_a_volt"] = decoder.decode_16bit_uint() / 10.0
                        
                        r209 = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_a_start_hour"] = r209 & 0xFF
                        data["setting_peak_shaving_a_start_minute"] = r209 >> 8
                        
                        r210 = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_a_end_hour"] = r210 & 0xFF
                        data["setting_peak_shaving_a_end_minute"] = r210 >> 8
                        
                        r211 = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_b_start_hour1"] = r211 & 0xFF
                        data["setting_peak_shaving_b_start_minute1"] = r211 >> 8
                        
                        r212 = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_b_end_hour1"] = r212 & 0xFF
                        data["setting_peak_shaving_b_end_minute1"] = r212 >> 8
                        
                        data["setting_smart_load_on_volt"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_smart_load_off_volt"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_smart_load_on_soc"] = decoder.decode_16bit_uint()
                        data["setting_smart_load_off_soc"] = decoder.decode_16bit_uint()
                        data["setting_start_pv_power"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_peak_shaving_b_soc"] = decoder.decode_16bit_uint()
                        data["setting_peak_shaving_b_volt"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_ac_couple_start_soc"] = decoder.decode_16bit_uint()
                        data["setting_ac_couple_end_soc"] = decoder.decode_16bit_uint()
                        data["setting_ac_couple_start_volt"] = decoder.decode_16bit_uint() / 10.0
                        data["setting_ac_couple_end_volt"] = decoder.decode_16bit_uint() / 10.0
                        
                        r224 = decoder.decode_16bit_uint()
                        data["hardware_lcd_version"] = r224 & 0xFF
                        data["hardware_lcd_screen_type"] = (r224 >> 8) & 0x03
                        data["hardware_lcd_model_code"] = (r224 >> 10) & 0x3F
                        
                        decoder.skip_registers(1) # 225
                        
                        r226 = decoder.decode_16bit_uint()
                        data["setting_func3_exct_en"] = (r226 >> 2) & 1
                        data["setting_func3_runwithoutgrid"] = (r226 >> 3) & 1
                        data["setting_func3_nperlyen"] = (r226 >> 4) & 1
                        
                        data["setting_bat_stop_charge_soc"] = decoder.decode_16bit_uint()
                        data["setting_bat_stop_charge_volt"] = decoder.decode_16bit_uint() / 10.0

                    # --- Block 7: Register 233 ---
                    result = client.read_holding_registers(233, count=1, **self._kwargs)
                    if not result.isError():
                        updated = True
                        data["setting_ac_charge_sporadic_charge"] = result.registers[0] & 0x01
                    else:
                        _LOGGER.warning("Modbus read error on holding register 233")

            except IndexError:
                _LOGGER.warning("IndexError during Modbus decoding. Inverter response may be shorter than expected.")
            except ConnectionException as ex:
                _LOGGER.error(f"Modbus connection failed during update: {ex}")
                return self.data # Return last known data
            except Exception as e:
                _LOGGER.error(f"An unexpected error occurred during Modbus update: {e}")
                return self.data # Return last known data


        # --- Generic Spike/Outlier Filter ---
        if updated:
            for key, new_val in list(data.items()):
                old_val = self.data.get(key)
                
                # Only apply to numeric values that have a previous baseline
                if old_val is None or not isinstance(old_val, (int, float)) or not isinstance(new_val, (int, float)):
                    self._consecutive_rejects[key] = 0
                    continue
                
                # Skip settings, raw packed cells/sensors indices, index helper fields, and serial numbers
                if key.startswith("setting_") or "cells" in key or "idx" in key or "serial" in key:
                    self._consecutive_rejects[key] = 0
                    continue
                    
                diff = abs(new_val - old_val)
                is_spike = False
                
                # Check for physically impossible outliers or massive unnatural jumps
                # (e.g. noise to 4000V, or dropping perfectly to 0 when it shouldn't)
                if "voltage" in key:
                    is_spike = diff > 40 or new_val > 600
                elif "power" in key:
                    is_spike = diff > 2000 or new_val > 5000
                elif "current" in key:
                    is_spike = diff > 10 or new_val > 100
                elif "frequency" in key:
                    is_spike = diff > 2 or new_val > 62 or (new_val < 40 and new_val != 0)
                elif "temperature" in key:
                    is_spike = diff > 5 or new_val > 100 or new_val < -50
                elif "battery_soc" in key or "battery_soh" in key:
                    # SOC/SOH change very slowly. An instant jump or drop of >5% is physically impossible
                    is_spike = diff > 5 or new_val > 100
                elif "energy" in key:
                    # Energy should not jump instantly, but allowed to drop to 0 at midnight.
                    # A drop to 0 will be treated as a spike and delayed by 3 polls (30 seconds),
                    # which is an acceptable delay for the daily reset while effectively filtering out 0-glitches.
                    is_spike = diff > 1.0

                if is_spike:
                    rejects = self._consecutive_rejects.get(key, 0) + 1
                    if rejects <= 2:
                        self._consecutive_rejects[key] = rejects
                        _LOGGER.debug(f"Spike detected for {key} (old: {old_val}, new: {new_val}). Rejecting {rejects}/2.")
                        # Revert the data dict to the old valid value
                        data[key] = old_val
                    else:
                        _LOGGER.debug(f"Spike persistently read for {key} (old: {old_val}, new: {new_val}). Accepting as valid change.")
                        self._consecutive_rejects[key] = 0
                else:
                    self._consecutive_rejects[key] = 0

            # --- Final Calculations ---
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
            data['energy_daily_grid_net'] = data.get('energy_daily_grid_import', 0) - data.get('energy_daily_grid_export', 0)
            data['energy_cumulative_grid_net'] = data.get('energy_cumulative_grid_import', 0) - data.get('energy_cumulative_grid_export', 0)

            self.data = data
            return self.data
        
        _LOGGER.warning("Modbus update failed to read any new data, returning last known values.")
        return self.data


    # Map of holding register address -> list of (data_key, bit_shift) tuples
    # used to reconstruct the raw register value from cached data.
    _REG_BIT_FIELDS: dict[int, list[tuple[str, int]]] = {
        21: [
            ("setting_func_en_eps", 0),
            ("setting_func_en_ovf_load_derate", 1),
            ("setting_func_en_drms", 2),
            ("setting_func_en_lvrt", 3),
            ("setting_func_en_anti_island", 4),
            ("setting_func_en_neutral_detect", 5),
            ("setting_func_en_grid_on_power_ss", 6),
            ("setting_func_en_ac_charge", 7),
            ("setting_func_en_sw_seamlessly", 8),
            ("setting_func_en_set_to_standby", 9),
            ("setting_func_en_forced_dischg", 10),
            ("setting_func_en_forced_chg", 11),
            ("setting_func_en_iso", 12),
            ("setting_func_en_gfci", 13),
            ("setting_func_en_dci", 14),
            ("setting_func_en_feed_in_grid", 15),
        ],
        110: [
            ("setting_functionen1_ubpvgridoffen", 0),
            ("setting_functionen1_ubfastzeroexport", 1),
            ("setting_functionen1_ubmicrogriden", 2),
            ("setting_functionen1_ubbatshared", 3),
            ("setting_functionen1_ubchglasten", 4),
            ("setting_functionen1_ctsampleratio", 5),   # 2-bit field (bits 5-6)
            ("setting_functionen1_buzzeren", 7),
            ("setting_functionen1_pvctsampletype", 8),  # 2-bit field (bits 8-9)
            ("setting_functionen1_takeloadtogether", 10),
            ("setting_functionen1_ongridworkingmode", 11),
            ("setting_functionen1_pvctsampleratio", 12), # 2-bit field (bits 12-13)
            ("setting_functionen1_greenmodeen", 14),
            ("setting_functionen1_ecomodeen", 15),
        ],
        120: [
            ("setting_half_hour_ac_chr_start_en", 0),
            ("setting_ac_charge_type", 1),
            ("setting_discharge_control_type", 4),
            ("setting_ongrid_eod_type", 6),
            ("setting_generator_charge_type", 7),
            ("setting_separate_zero_export_en", 8),
        ],
        126: [
            ("setting_hourly_charge_discharge_time_0", 0),
            ("setting_hourly_charge_discharge_time_1", 2),
            ("setting_hourly_charge_discharge_time_2", 4),
            ("setting_hourly_charge_discharge_time_3", 6),
            ("setting_hourly_charge_discharge_time_4", 8),
            ("setting_hourly_charge_discharge_time_5", 10),
            ("setting_hourly_charge_discharge_time_6", 12),
            ("setting_hourly_charge_discharge_time_7", 14),
        ],
        127: [
            ("setting_hourly_charge_discharge_time_8", 0),
            ("setting_hourly_charge_discharge_time_9", 2),
            ("setting_hourly_charge_discharge_time_10", 4),
            ("setting_hourly_charge_discharge_time_11", 6),
            ("setting_hourly_charge_discharge_time_12", 8),
            ("setting_hourly_charge_discharge_time_13", 10),
            ("setting_hourly_charge_discharge_time_14", 12),
            ("setting_hourly_charge_discharge_time_15", 14),
        ],
        128: [
            ("setting_hourly_charge_discharge_time_16", 0),
            ("setting_hourly_charge_discharge_time_17", 2),
            ("setting_hourly_charge_discharge_time_18", 4),
            ("setting_hourly_charge_discharge_time_19", 6),
            ("setting_hourly_charge_discharge_time_20", 8),
            ("setting_hourly_charge_discharge_time_21", 10),
            ("setting_hourly_charge_discharge_time_22", 12),
            ("setting_hourly_charge_discharge_time_23", 14),
        ],
        129: [
            ("setting_hourly_charge_discharge_time_24", 0),
            ("setting_hourly_charge_discharge_time_25", 2),
            ("setting_hourly_charge_discharge_time_26", 4),
            ("setting_hourly_charge_discharge_time_27", 6),
            ("setting_hourly_charge_discharge_time_28", 8),
            ("setting_hourly_charge_discharge_time_29", 10),
            ("setting_hourly_charge_discharge_time_30", 12),
            ("setting_hourly_charge_discharge_time_31", 14),
        ],
        130: [
            ("setting_hourly_charge_discharge_time_32", 0),
            ("setting_hourly_charge_discharge_time_33", 2),
            ("setting_hourly_charge_discharge_time_34", 4),
            ("setting_hourly_charge_discharge_time_35", 6),
            ("setting_hourly_charge_discharge_time_36", 8),
            ("setting_hourly_charge_discharge_time_37", 10),
            ("setting_hourly_charge_discharge_time_38", 12),
            ("setting_hourly_charge_discharge_time_39", 14),
        ],
        131: [
            ("setting_hourly_charge_discharge_time_40", 0),
            ("setting_hourly_charge_discharge_time_41", 2),
            ("setting_hourly_charge_discharge_time_42", 4),
            ("setting_hourly_charge_discharge_time_43", 6),
            ("setting_hourly_charge_discharge_time_44", 8),
            ("setting_hourly_charge_discharge_time_45", 10),
            ("setting_hourly_charge_discharge_time_46", 12),
            ("setting_hourly_charge_discharge_time_47", 14),
        ],
        179: [
            ("setting_ufunctionen2_grid_peak_shaving", 7),
            ("setting_ufunctionen2_gen_peak_shaving", 8),
            ("setting_ufunctionen2_bat_chg_control", 9),
            ("setting_ufunctionen2_bat_dischg_control", 10),
            ("setting_ufunctionen2_ac_coupling", 11),
            ("setting_ufunctionen2_pv_arc_en", 12),
            ("setting_ufunctionen2_smart_load_en", 13),
            ("setting_ufunctionen2_rsd_disable", 14),
            ("setting_ufunctionen2_ongrid_always_on", 15),
        ],
        233: [
            ("setting_ac_charge_sporadic_charge", 0),
        ],
    }

    def _reconstruct_register(self, address: int) -> Optional[int]:
        """Reconstruct the raw 16-bit register value from cached data bit fields."""
        fields = self._REG_BIT_FIELDS.get(address)
        if fields is None:
            _LOGGER.warning(f"No cached bit-field map for register {address}. Cannot reconstruct.")
            return None

        raw = 0
        for key, shift in fields:
            val = self.data.get(key)
            if val is None:
                _LOGGER.warning(f"Cached key '{key}' missing for register {address} reconstruction.")
                return None
            raw |= (int(val) << shift)
        return raw

    def write_masked_register(self, address: int, value: int, mask: int) -> bool:
        """Read-Modify-Write a masked register using cached register data.

        Reads the current register value from the last poll cache (no live
        Modbus read required), applies the mask, then queues the write.
        """
        current_val = self._reconstruct_register(address)
        if current_val is None:
            _LOGGER.error(
                f"Could not reconstruct register {address} from cache for RMW. "
                "Ensure at least one poll has completed."
            )
            return False

        shift = 0
        temp_mask = mask
        while (temp_mask & 1) == 0 and temp_mask > 0:
            temp_mask >>= 1
            shift += 1

        shifted_val = (value << shift) & mask
        new_val = (current_val & ~mask) | shifted_val

        _LOGGER.debug(f"RMW Address {address}: CachedOld={current_val:#06x}, Mask={mask:#06x}, Shift={shift}, NewVal={new_val:#06x}")

        return self.write_register(address, new_val)

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