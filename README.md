[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![HACS][hacsbadge]][hacs]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

# Home Assistant EG4 Inverter Modbus 

This is a custom Home Assistant integration for monitoring EG4 inverter systems locally via Modbus.  It allows you to remove any reliance on the cloud and disconnect your dongle from your inverter.  This is the best strategy for ensuring security, privacy, and resilience. 


## Features

This integration allows you to:

- **Local Only Communications**: Remove your dongle and no longer be worried about any external connection to your electrical infrastructure
- **See Real-Time Data**: View your solar production, battery levels, grid usage, and power consumption
- **Track Energy Usage**: Monitor daily, monthly, and lifetime energy statistics
- **Create Automations**: Automatically respond to changing energy conditions


## HACS Installation


[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=EG4-Inverter-Modbus&owner=poldim)


1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/poldim/EG4-Inverter-Modbus`
3. Category: Integration
4. Search for "EG4 Inverter Modbus" and install
5. Restart Home Assistant


## Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"EG4 Inverter Modbus"**
3. Enter the name for your inverter, host IP, port, and slave for your inverter


## Background

I've got a 12KPV and want to pull the data locally without the use of the dongle/cloud connection.  This integration allows me to pull values into HA, which then go into historical storage/trending in Influx/Grafana. 

Just sharing what is working for me.  I don't know how to write code, and have no idea what I'm doing.  Use at your own risk.  Please feel free to correct and fix anything in here via PRs.  


## Additional Information:

# Sensors


### Standard sensors:  Most useful for most applications, individual sensors can be enabled via GUI in HA

```yaml
AC Input Type
Battery Cycle Count
Battery SOC
Battery SOH
BMS Current Battery
BMS Temperature Max Cell
BMS Temperature Min Cell
BMS Voltage Max Cell
BMS Voltage Min Cell
Current Inverter RMS
Energy Cumulative PV
Energy Daily AC Charge
Energy Daily Battery Charge
Energy Daily Battery Discharge
Energy Daily Grid Export
Energy Daily Grid Import
Energy Daily Inverter
Energy Daily Inverter Output
Energy Daily PV Total
Energy Daily PV1
Inverter State
Power AC Charge
Power Battery Charge
Power Battery Discharge
Power Battery Total
Power Grid Export
Power Grid Import
Power Grid Total
Power Inverter
Power Inverter Output
Power PV Total
Power PV1
Temperature Internal
Voltage Battery
Voltage Grid L1
Voltage Inverter L1-L2
Voltage PV Average
Voltage PV1
Fault Code
Inverter ON time
Warning Code
```


### Disabled Sensors: These sensors are available but disabled by default

```yaml
AFCI Arc CH1
AFCI Arc CH2
AFCI Arc CH3
AFCI Arc CH4
AFCI Max Arc CH1
AFCI Max Arc CH2
AFCI Max Arc CH3
AFCI Max Arc CH4
Current AFCI CH1
Current AFCI CH2
Current AFCI CH3
Current AFCI CH4
Energy Cumulative AC Charge
Energy Cumulative Battery Charge
Energy Cumulative Battery Discharge
Energy Cumulative Generator
Energy Cumulative Grid Export
Energy Cumulative Grid Import
Energy Cumulative Inverter
Energy Cumulative Inverter L1-N
Energy Cumulative Inverter L2-N
Energy Cumulative Inverter Output
Energy Cumulative PV1
Energy Cumulative PV2
Energy Cumulative PV3
Energy Daily Generator
Energy Daily Inverter L1-N
Energy Daily Inverter L2-N
Energy Daily PV2
Energy Daily PV3
Frequency Generator
Frequency Grid
Frequency Inverter
Heatsink Temperature AC
Heatsink Temperature DC
Inverter Uptime (minutes)
Power Apparent Inverter
Power Apparent Inverter L1-N
Power Apparent Inverter L2-N
Power Factor Inverter
Power Generator
Power Inverter L1-N
Power Inverter L2-N
Power PV2
Power PV3
Temperature Battery
Temperature T1
Temperature T2
Temperature T3
Temperature T4
Temperature T5
Voltage Battery Sample Inverter
Voltage Bus 1
Voltage Bus 2
Voltage Bus P
Voltage Generator
Voltage Grid L2
Voltage Grid L3
Voltage Inverter L1-N
Voltage Inverter L2-L3
Voltage Inverter L2-N
Voltage Inverter L3-L1
Voltage PV2
Voltage PV3
```



### Experimental and NOT RECOMMENDED - Inverter configuration sensors, use at your own risk!

```yaml
AC Charge Battery Current
AC Charge End SOC
AC Charge End Voltage
AC Charge Percentage
AC Charge Start SOC
AC Charge Start Voltage
AC Charging SOC Limit
Battery Capacity
Battery Low Back SOC
Battery Low Back Voltage
Battery Low SOC
Battery Low to Utility SOC
Battery Low to Utility Voltage
Battery Low Voltage
Battery Nominal Voltage
Charge Current
Charge Power Percentage
Charge Voltage Reference
Discharge Current
Discharge Cutoff Voltage
Discharge Power Percentage
EOD SOC
Equalization Interval
Equalization Time
Equalization Voltage
Float Charge Voltage
Gen Charge End SOC
Gen Charge End Voltage
Gen Charge Start SOC
Gen Charge Start Voltage
Gen Rated Power
Grid Connection Wait Time
Inverter Frequency
Inverter Voltage
Language
Line Mode
Max Backflow Power
Max Gen Charge Battery Current
Max Grid Input Power
Ongrid EOD Voltage
Output Priority Config
Power Offset WCT
Ptouser Start Discharge
PV Input Model
PV Start Voltage
Reconnection Wait Time
SOC Low Limit Inverter Discharge
System Type
Voltage Start Derating
```

# Wiring for Communications

The overall path is:
```yaml
12KPV Inverter Modbus RJ45 Port --> Modbus to Ethernet Gateway --> POE Network Switch
```
I use a Modbus to Ethernet gateway to my inverter ([link]([url](https://amzn.to/3KThRJn))).  This was initially connected in parallel with my dongle, and then after I confirmed it worked, I replaced the dongle.  Running them in parallel had no negative impact on my system.

![Dashboard Screenshot](docs/12KPV%20Comms%20Wiring.png)

# Inverter Firmware Updates

In the future, if you want to do any inverter update, you have two options:  
1) Via USB stick
2) Plug in your dongle back into the HDMI port, perform the update, then remove the dongle.

# License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)

## Disclaimer

Unofficial integration not affiliated with EG4 Electronics. 


[releases-shield]: https://img.shields.io/github/v/release/poldim/EG4-Inverter-Modbus?style=for-the-badge
[releases]: https://github.com/poldim/EG4-Inverter-Modbus/releases
[license-shield]: https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey?style=for-the-badge
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[hacs]: https://hacs.xyz
[maintenance-shield]: https://img.shields.io/badge/maintainer-poldim-blue?style=for-the-badge
[user_profile]: https://github.com/poldim
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[buymecoffee]: https://buymeacoffee.com/DKhazz
