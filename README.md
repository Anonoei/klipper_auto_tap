# Klipper Auto TAP
 Klipper module for automatic z-offset configuration on [Voron TAP](https://github.com/VoronDesign/Voron-Tap)

**This module is under development**: Please ensure the calculated offset seems reasonable for your printer! See [Validate Results](https://github.com/klipper_auto_tap#validate_results) for how to validate the offset.

This module calculates the distance your toolhead lifts to actuate TAP. 
Doing this enables *automatic z-offset calculation*. i.e. make `G0 Z0.2` put the nozzle at 0.2mm above the bed. 
This is a fairly slow process since the toolhead needs to move by *step* (0.005), check if the endstop is still triggered, and repeat. 
Check [how it works](https://github.com/anonoei/klipper_auto_tap#how-does-it-work) for more information. 

On textured PEI, the offset may need to be slightly lowered to get proper first-layer squish. 
YMMV.

This is only known to work on QGL based printers, namely the Voron 2. 
If you use a different printer and want to help add support, please create an [issue](https://github.com/Anonoei/klipper_auto_tap/issues), or message me on Discord. 
Please include Auto TAP's console output so I can try to fix the issue.

## Known issues
 - [Issue 2](https://github.com/Anonoei/klipper_auto_tap/issues/2): TILT_ADJUST printers calculate wrong offset
   - If you run a trident, or other printer that uses something other than QGL for leveling, the results won't be accurate.
 - [Issue 5](https://github.com/Anonoei/klipper_auto_tap/issues/5): TAP implementation changes expected offset
   - Different implementations of TAP (CL CNC, Mellow CNC, stock) have different expected offsets, the results may not be accurate depending on what version of tap you are using. Please [validate results](https://github.com/klipper_auto_tap#validate_results).

# Table of Contents
 - [Overview](https://github.com/Anonoei/klipper_auto_tap#overview)
 - [How does it work](https://github.com/Anonoei/klipper_auto_tap#how-does-it-work)
 - [Using Klipper Auto TAP](https://github.com/Anonoei/klipper_auto_tap#using-klipper-auto-tap)
   - [Installation](https://github.com/Anonoei/klipper_auto_tap#installation)
     - [Moonraker Update Manager](https://github.com/Anonoei/klipper_auto_tap#moonraker-update-manager)
   - [Configuration](https://github.com/Anonoei/klipper_auto_tap#configuration)
   - [Macro](https://github.com/Anonoei/klipper_auto_tap#macro)
   - [Validate Results](https://github.com/Anonoei/klipper_auto_tap#validate-results)
   - [Example usage](https://github.com/Anonoei/klipper_auto_tap#example-usage)

## Overview
 - License: MIT


## How does it work?
1. Home your printer
   - When your printer homes Z, your toolhead is lifted until the endstop is triggered, making that lifted point your z0
2. Move to park position
3. For each sample, tap!
   1. Probe the bed, and keep it at the position where endstop triggers
   2. Slowly lift the toolhead by *step* until the endstop isn't triggered
   3. Calculate travel distance *travel* = `abs(probe z - measure distance)`
   4. Save the resulting probe, measure distance, and travel
4. Calculate Z-Offset based on `CALC_METHOD`
   - QGL: `travel_mean * 2`
   - STA: `measure_mean + (travel_mean/2)` (under development)

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

### Moonraker Update Manager

```
[update_manager klipper_auto_tap]
type: git_repo
path: ~/klipper_auto_tap
origin: https://github.com/anonoei/klipper_auto_tap.git
primary_branch: main
install_script: install.sh
managed_services: klipper
```

### Configuration
 To configure auto tap you need to specify which version of TAP you are running
 Name               | tap_version | Validated
 ------------------ | ----------- | ---------
 ChaoticLab CNC Tap | CL_CNC      | True
 Voron Tap R8       | R8          | False
 Voron Tap R6       | R6          | False
If your version of tap is not validated, please [validate results] before using the calculated offset, and let me know.


Then, place this in your printer.cfg
```
[auto_tap]
tap_version: <your tap_version>
```
The values listed below are the defaults Auto TAP uses. You can include them if you wish to change their values, or run into issues.
```
[auto_tap]
tap_version: <your version> ; Set during the first part of configuration
x: Unset                    ; X position to probe, Defaults to the middle of the x axis `(max - min)/2`
y: Unset                    ; Y position to probe, Defaults to the middle of the y axis `(max - min)/2`
z: 10                       ; Z position to park
probe_to: -2                ; Lower probe until it triggers, or reaches this value
set: True                   ; Set probe offset after calculation
settling_probe: True        ; Perform a dummy probe before starting
stop: 2.0                   ; Lift Z up to this amount for TAP to de-actuate
step: 0.005                 ; Lift Z by this amount each check
samples: Unset              ; Number of samples to take, Defaults to your config's probe sample count
retract: Unset              ; Lift up by this amount at end, Defaults to your config's probe retract distance
probe_speed: Unset          ; Probe at this speed, Defaults to your config's probe travel speed
lift_speed: Unset           ; Retract at this speed, Defaults to your config's probe lift speed
travel_speed: 1000          ; Speed for travel to park position
```
### Macro
Run the klipper command `AUTO_TAP`. You can also use the arguments below
Argument       | Default | Description
-------------- | ------- | -----------
TAP_VERSION    | Unset   | Defaults to the configuration value. You can use this to try other offsets.
X              | Unset   | X position to probe, Defaults to the middle of the x axis `(max - min)/2`
Y              | Unset   | Y position to probe, Defaults to the middle of the y axis `(max - min)/2`
Z              | 10      | Z position to park
PROBE_TO       | -2      | Lower probe until it triggers, or reaches this value
SET            | 1       | Set probe offset after calculation
SETTLING_PROBE | 1       | Perform a dummy probe before starting
STOP           | 2.0     | Lift Z up to this amount for TAP to de-actuate
STEP           | 0.005   | Lift Z by this amount each check
SAMPLES        | Unset   | Number of samples to take, Defaults to your config's probe sample count
RETRACT        | Unset   | Lift up by this amount at end, Defaults to your config's probe retract distance
PROBE_SPEED    | 1.0     | Probe at this speed
LIFT_SPEED     | Unset   | Retract at this speed, Defaults to your config's probe lift speed
TRAVEL_SPEED   | 1000    | Speed for travel to park position
FORCE          | 0       | Force AUTO_TAP to run, even if it was calculated previously

If you set values under *Configuration*, those will become the defaults.

If you run `AUTO_TAP` again, it will set the z-offset to the last calculated value unless you run `AUTO_TAP FORCE=1`.

### Validate Results
 After `AUTO_TAP` is run, by default it will apply the calculated offset.
 1. Run `G0 Z`*(first layer height)*
    - I use a first layer height of 0.25, so it's `G0 Z0.25`
 2. Verify there is a gap between the tip of the nozzle and the build surface, and it looks close to the Z distance you moved the toolhead to
 3. If your nozzle is touching the bed **DO NOT USE THIS OFFSET**
    1. Try running `AUTO_TAP FORCE=1`, and re-validate
    2. Create an [issue](https://github.com/Anonoei/klipper_auto_tap/issues). Please include Auto TAP's console output and your printer model

### Example Usage
One and done:
1.  Run `AUTO_TAP`, and [validate the offset](https://github.com/klipper_auto_tap#validate_results)
2.  Run `Z_OFFSET_APPLY_PROBE` to save the offset.
3.  Restart your printer
4.  Adjust as needed based on build surface material


Before starting print:
1.  Open your printers configuration
2.  In your `PRINT_START` macro, add `AUTO_TAP` after homing and leveling have been complete
3.  Adjust as needed based on build surface material