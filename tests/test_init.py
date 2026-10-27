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

    # 3. Manually disable entity_enabled as a USER
    registry.async_update_entity(
        entry_enabled.entity_id,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    assert registry.async_get(entry_enabled.entity_id).disabled_by == er.RegistryEntryDisabler.USER

    # When "enable all" is turned on again, user-disabled entity must remain disabled by USER
    new_options.update({
        "enable_all_read_sensors": True,
        "enable_write_sensors": True,
    })
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)

    await _update_entity_registry(hass, mock_config_entry)

    entity_enabled = registry.async_get(entry_enabled.entity_id)
    entity_disabled = registry.async_get(entry_disabled.entity_id)
    assert entity_enabled.disabled_by == er.RegistryEntryDisabler.USER
    assert entity_disabled.disabled_by is None


async def test_unchecking_enable_write_sensors_disables_all_write_entities(hass: HomeAssistant, mock_modbus_client, mock_config_entry):
    """Test that toggling 'Enable Write Sensors' swaps between writable entities and read-only sensors."""
    from custom_components.eg4_inverter_modbus.number import async_setup_entry as async_setup_number
    from custom_components.eg4_inverter_modbus.select import async_setup_entry as async_setup_select
    from custom_components.eg4_inverter_modbus.time import async_setup_entry as async_setup_time
    from custom_components.eg4_inverter_modbus.sensor import (
        async_setup_entry as async_setup_sensor,
        EG4ReadOnlyHoldingSensor,
    )

    mock_config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    name = mock_config_entry.data[CONF_NAME]

    hub = EG4ModbusHub(hass, name, "10.0.0.100", 502, 1, 10)
    hass.data[DOMAIN] = {mock_config_entry.entry_id: hub}

    # 1. Test platform setup with enable_write_sensors = False
    new_options = dict(mock_config_entry.options)
    new_options["enable_write_sensors"] = False
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)

    added_numbers = []
    added_selects = []
    added_times = []
    added_sensors = []

    await async_setup_number(hass, mock_config_entry, lambda entities: added_numbers.extend(entities))
    await async_setup_select(hass, mock_config_entry, lambda entities: added_selects.extend(entities))
    await async_setup_time(hass, mock_config_entry, lambda entities: added_times.extend(entities))
    await async_setup_sensor(hass, mock_config_entry, lambda entities: added_sensors.extend(entities))

    assert len(added_numbers) > 0
    assert len(added_selects) > 0
    assert len(added_times) > 0

    # All write entities must have entity_registry_enabled_default as False when unchecked
    for entity in added_numbers + added_selects + added_times:
        assert entity.entity_registry_enabled_default is False, f"{entity.unique_id} write entity enabled by default when unchecked!"

    # Mirror sensors for writable registers must have entity_registry_enabled_default as True when unchecked
    mirror_sensors = [s for s in added_sensors if isinstance(s, EG4ReadOnlyHoldingSensor)]
    assert len(mirror_sensors) > 0
    for entity in mirror_sensors:
        assert entity.entity_registry_enabled_default is True, f"{entity.unique_id} read-only mirror sensor disabled by default when unchecked!"
        assert entity.entity_category != er.EntityCategory.CONFIG, f"{entity.unique_id} sensor entity category cannot be CONFIG!"

    # 2. Test platform setup with enable_write_sensors = True
    new_options["enable_write_sensors"] = True
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)

    added_numbers_true = []
    added_selects_true = []
    added_times_true = []
    added_sensors_true = []

    await async_setup_number(hass, mock_config_entry, lambda entities: added_numbers_true.extend(entities))
    await async_setup_select(hass, mock_config_entry, lambda entities: added_selects_true.extend(entities))
    await async_setup_time(hass, mock_config_entry, lambda entities: added_times_true.extend(entities))
    await async_setup_sensor(hass, mock_config_entry, lambda entities: added_sensors_true.extend(entities))

    for entity in added_numbers_true + added_selects_true + added_times_true:
        assert entity.entity_registry_enabled_default is True, f"{entity.unique_id} write entity disabled by default when checked!"

    mirror_sensors_true = [s for s in added_sensors_true if isinstance(s, EG4ReadOnlyHoldingSensor)]
    for entity in mirror_sensors_true:
        assert entity.entity_registry_enabled_default is False, f"{entity.unique_id} read-only mirror sensor enabled by default when checked!"

    # Reset back to False for registry toggle testing
    new_options["enable_write_sensors"] = False
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)

    # 3. Test _update_entity_registry when write entities and mirror sensors are registered
    sample_write_unique_ids = [
        # Controls (selects)
        ("select", f"{name}_setting_func_en_forced_dischg"),
        ("select", f"{name}_setting_ufunctionen2_export_pv_only"),
        ("select", f"{name}_setting_func_en_set_to_standby"),
        ("select", f"{name}_setting_ac_charge_sporadic_charge"),
        # Configuration numbers
        ("number", f"{name}_setting_forced_discharge_power"),
        ("number", f"{name}_setting_forced_discharge_stop_soc"),
        ("number", f"{name}_setting_force_dischg_end_volt"),
        # Configuration times
        ("time", f"{name}_setting_ac_charge_t1_start"),
        ("time", f"{name}_setting_forced_discharge_t1_start"),
        ("time", f"{name}_setting_peak_shaving_a_start"),
    ]

    registered_write_entries = []
    registered_mirror_entries = []
    for domain, uid in sample_write_unique_ids:
        # Pre-populate write entity as currently enabled in registry
        entry_reg = registry.async_get_or_create(
            domain=domain,
            platform=DOMAIN,
            unique_id=uid,
            config_entry=mock_config_entry,
        )
        registered_write_entries.append(entry_reg)

        # Pre-populate mirror read-only sensor as currently disabled and with CONFIG category in registry
        mirror_reg = registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=uid,
            config_entry=mock_config_entry,
            disabled_by=er.RegistryEntryDisabler.INTEGRATION,
            entity_category=er.EntityCategory.CONFIG,
        )
        registered_mirror_entries.append(mirror_reg)

    # When enable_write_sensors is False:
    # - writable entities must be disabled
    # - read-only mirror sensors must be enabled
    # - any mirror sensors erroneously saved with CONFIG category must be migrated to DIAGNOSTIC
    await _update_entity_registry(hass, mock_config_entry)

    for entry_reg in registered_write_entries:
        item = registry.async_get(entry_reg.entity_id)
        assert item.disabled_by == er.RegistryEntryDisabler.INTEGRATION, f"{entry_reg.unique_id} was not disabled!"

    for mirror_reg in registered_mirror_entries:
        item = registry.async_get(mirror_reg.entity_id)
        assert item.disabled_by is None, f"{mirror_reg.unique_id} read-only mirror was not enabled!"
        assert item.entity_category != er.EntityCategory.CONFIG, f"{mirror_reg.unique_id} still has CONFIG category!"
        assert item.entity_category == er.EntityCategory.DIAGNOSTIC, f"{mirror_reg.unique_id} not migrated to DIAGNOSTIC!"

    # 4. When enable_write_sensors is toggled to True:
    # - writable entities must be enabled
    # - read-only mirror sensors must be disabled
    new_options["enable_write_sensors"] = True
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
    await _update_entity_registry(hass, mock_config_entry)

    for entry_reg in registered_write_entries:
        item = registry.async_get(entry_reg.entity_id)
        assert item.disabled_by is None, f"{entry_reg.unique_id} was not re-enabled!"

    for mirror_reg in registered_mirror_entries:
        item = registry.async_get(mirror_reg.entity_id)
        assert item.disabled_by == er.RegistryEntryDisabler.INTEGRATION, f"{mirror_reg.unique_id} read-only mirror was not disabled!"

    # 5. When enable_write_sensors is unchecked again (False):
    # - writable entities must be disabled again
    # - read-only mirror sensors must be re-enabled
    new_options["enable_write_sensors"] = False
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
    await _update_entity_registry(hass, mock_config_entry)

    for entry_reg in registered_write_entries:
        item = registry.async_get(entry_reg.entity_id)
        assert item.disabled_by == er.RegistryEntryDisabler.INTEGRATION, f"{entry_reg.unique_id} was not disabled on toggle off!"

    for mirror_reg in registered_mirror_entries:
        item = registry.async_get(mirror_reg.entity_id)
        assert item.disabled_by is None, f"{mirror_reg.unique_id} read-only mirror was not re-enabled on toggle off!"

