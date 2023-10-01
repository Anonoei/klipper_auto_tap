# Klipper Auto TAP
 Automatically find Voron TAP's probe offset

# Description
 - Intent: Create an easy to use, automated way to find Voron TAP's probe offset

# Overview
 - License: MIT

# Development status/roadmap
 - [ ] Initial release

# Using Klipper Auto TAP
## Installation
```
cd ~
cd klipper_auto_tap
git clone https://github.com/Anonoei/klipper_auto_tap.git
./install.sh
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