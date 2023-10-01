#!/bin/bash

# Force script to exit if an error occurs
set -e

KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

# Verify we're running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "This script must not run as root"
    exit -1
fi

# Check if Klipper is installed
if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
    echo "Klipper service found!"
else
    echo "Klipper service not found, please install Klipper first"
    exit -1
fi

# Link auto_tap to klipper
echo "Linking auto tap to Klipper..."
ln -sf "${SRCDIR}/${extension}" "${KLIPPER_PATH}/klippy/extras/auto_tap.py"

# Restart klipper
echo "Restarting Klipper..."
sudo systemctl restart klipper