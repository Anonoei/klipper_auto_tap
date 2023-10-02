# Klipper Auto TAP
 Automatically find Voron TAP's probe offset

# Table of Contents
 - [Description](https://github.com/anonoei/klipper_auto_tap#description)
 - [Overview](https://github.com/anonoei/klipper_auto_tap#overview)
 - [Development status](https://github.com/anonoei/klipper_auto_tap#development-statusroadmap)
 - [Using Klipper Auto TAP](https://github.com/anonoei/klipper_auto_tap#using-klipper-auto-tap)
   - [Installation](https://github.com/anonoei/klipper_auto_tap#installation)
   - [Configuration](https://github.com/anonoei/klipper_auto_tap#configuration)
   - [Macro](https://github.com/anonoei/klipper_auto_tap#macro)
   - [Moonraker Update Manager](https://github.com/anonoei/klipper_auto_tap#moonraker-update-manager)

# Description
 - Intent: Create an easy to use, automated way to find Voron TAP's probe offset

# Overview
 - License: MIT

# Development status/roadmap
 - [ ] Initial release

# Using Klipper Auto TAP
## Installation
To install this module, you need to clone the repository and run the `install.sh` script
### Automatic installation
```
cd ~
git clone https://github.com/Anonoei/klipper_auto_tap.git
cd klipper_auto_tap
./install.sh
```
### Manual installation
```
cd ~
git clone https://github.com/Anonoei/klipper_auto_tap.git
cd klipper_auto_tap
ln -sf ~/klipper_auto_tap/auto_tap.py ~/klipper/klippy/extras/auto_tap.py
sudo systemctl restart klipper
```

## Configuration
Place this in your printer.cfg
```
[auto_tap]
```
Optionally, you can include these definitions instead of using the macro arguments
```
[auto_tap]
start: 0.5
stop: -0.5
step: -0.0125
set_at_end: False
samples: 5
probing_speed: 150
lift_speed: 300
```
## Macro
Run the klipper command `AUTO_TAP`. You can also use the arguments below
Argument    | Default | Description
----------- | ------- | -----------
START       | 0.5     | Z height to start checking
STOP        | -0.5    | Z height to stop checking
STEP        | -0.0125 | Adjust Z by this amount each check
SET         | False   | Set probe offset after calcuation
SAMPLES     | 5       | How many times to check
PROBE_SPEED | None    | Speed when probing
LIFT_SPEED  | None    | Speed when lifting

## Moonraker Update Manager
```
[update_manager klipper_auto_tap]
type: git_repo
path: ~/klipper_auto_tap
origin: https://github.com/anonoei/klipper_auto_tap.git
managed_services: klipper
```