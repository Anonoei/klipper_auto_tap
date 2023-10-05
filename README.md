# Klipper Auto TAP
 Klipper module for automatic z-offset configuration on [Voron TAP](https://github.com/VoronDesign/Voron-Tap)

This extension calculates TAP's travel distance, i.e., the distance your toolhead lifts up to actuate TAP. Doing this enables *automatic z-offset calculation*. This allows the **absolute** offset to be measured, i.e. make `G0 Z0.2` put the nozzle at 0.2mm above the bed.

On textured PEI, the offset may need to be slightly lowered to get proper first-layer squish. YMMV. 

# Table of Contents
 - [Overview](https://github.com/anonoei/klipper_auto_tap#overview)
 - [How does it work](https://github.com/anonoei/klipper_auto_tap#how-does-it-work)
 - [Usage examples](https://github.com/anonoei/klipper_auto_tap#usage_examples)
 - [Using Klipper Auto TAP](https://github.com/anonoei/klipper_auto_tap#using-klipper-auto-tap)
   - [Installation](https://github.com/anonoei/klipper_auto_tap#installation)
   - [Configuration](https://github.com/anonoei/klipper_auto_tap#configuration)
   - [Macro](https://github.com/anonoei/klipper_auto_tap#macro)
   - [Moonraker Update Manager](https://github.com/anonoei/klipper_auto_tap#moonraker-update-manager)

## Overview
 - License: MIT
 - Testing:
   - Anonoei: [Voron 2.4 "Palladium"](https://github.com/anonoei/Palladium)


## How does it work?
1. Probe the bed
   - The distance this probe measures is your printer's z0
   - Since TAP presses the nozzle down into the bed, z0 will actuate TAP (and be a negative number to true z0)
2. Auto TAP, on each sample
   1.  Probe the bed, and save the measured value
   2.  Move the nozzle to the measured value, and raise it by *step* until TAP de-actuates
   3.  Save *travel* = `abs(probe z - measure distance)`
3. Calculate Z-Offset based on `CALC_METHOD`
   - QGL: `travel_mean \* 2`
   - STA: `measure_mean + (travel_mean/2)`

## Usage examples
One and done:
 - Run `AUTO_TAP`, and save the z-offset. Adjust as needed based on build surface material
Before starting print:
 - In your `PRINT_START` macro, add `AUTO_TAP` after homing and leveling have been complete

## Using Klipper Auto TAP
### Installation
To install this module, you need to clone the repository and run the `install.sh` script

#### Automatic installation
```
cd ~
git clone https://github.com/Anonoei/klipper_auto_tap.git
cd klipper_auto_tap
chmod +x install.sh
./install.sh
```
#### Manual installation
 1. Clone the repository
    1. `cd ~`
    2. `git clone https://github.com/Anonoei/klipper_auto_tap.git`
    3. `cd klipper_auto_tap`
 2. Link auto_tap to klipper
    1. `ln -sf ~/klipper_auto_tap/auto_tap.py ~/klipper/klippy/extras/auto_tap.py`
 3. Restart klipper
    1. `sudo systemctl restart klipper`

### Configuration
Place this in your printer.cfg
```
[auto_tap]
```
Optionally, you can include these definitions instead of using the macro arguments
```
[auto_tap]
x: 150
y: 150
z: 10
set: 1
settling_probe: 1
calc_method: <your printers leveling method, "QGL", or "STA">
stop: 1.0
step: 0.005
samples: <your config's probe sample count>
retract: <your config's probe retract distance>
probe_speed: <your config's probe travel speed>
lift_speed: <your config's probe lift speed>
travel_speed: 1000
```
### Macro
Run the klipper command `AUTO_TAP`. You can also use the arguments below
Argument       | Default | Description
-------------- | ------- | -----------
X              | 150     | X position to probe
Y              | 150     | Y position to probe
Z              | 10      | Z position to probe
SET            | 1       | Set probe offset after calculation
SETTLING_PROBE | 1       | Perform a dummy probe before starting
CALC_METHOD    | None    | Method to calculate z-offset
STOP           | 1.0     | Z height to stop checking
STEP           | 0.005   | Lift Z by this amount each check
SAMPLES        | None    | How many times to check
RETRACT        | None    | How far to retract z
PROBE_SPEED    | None    | Speed when probing
LIFT_SPEED     | None    | Speed when lifting
TRAVEL_SPEED   | 1000    | Speed when traveling
FORCE          | 0       | Force AUTO_TAP to run, even if it was calculated previously

If you set values under *Configuration*, those will become the defaults.

If you run `AUTO_TAP` again, it will set the z-offset to the last calculated value unless you run `AUTO_TAP FORCE=1`.

### Moonraker Update Manager
```
[update_manager klipper_auto_tap]
type: git_repo
path: ~/klipper_auto_tap
origin: https://github.com/anonoei/klipper_auto_tap.git
managed_services: klipper
```