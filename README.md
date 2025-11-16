# EG4-Inverter-Modbus

I've got a 12KPV and want to pull the data locally without the use of the dongle/cloud connection.  This integration allows me to pull values into HA, which then go into historical storage/trending in Influx/Grafana. 

Just sharing what is working for me.  I don't know how to write code, and have no idea what I'm doing.  Use at your own risk.  Please feel free to correct and fix anything in here via PRs.  

## Installation

### HACS (Recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/poldim/EG4-Inverter-Modbus`
3. Category: Integration
4. Search for "EG4 Inverter Modbus" and install
5. Restart Home Assistant

### Manual Installation

```bash
cd /config/custom_components
git clone https://github.com/poldim/EG4-Inverter-Modbus.git eg4_inverter_modbus
```

Restart Home Assistant after installation.

## Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"EG4 Inverter Modbus"**
3. Enter the name for your inverter, host IP, port, and slave for your inverter

# License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)

## Disclaimer

Unofficial integration not affiliated with EG4 Electronics. 
