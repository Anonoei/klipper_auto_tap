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
```
[auto_tap]
start: 0.5 # Z height to start checking
stop: -0.5 # Z height to stop checking if TAP doesn't actuate
step: -0.0125 # Adjust Z height by this amount each check
accuracy: 1000 # Internal use, converts above values to ints
set_at_end: False # Set probe offset after calculation
samples: 5 # How many times to check
probing_speed: 150 # Speed when probing
lift_speed: 300 # Speed when lifting
```