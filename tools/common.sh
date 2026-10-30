#!/bin/sh
# Shared helpers for FocusPix CLI deploy scripts (no IDE).
# Source with: . "$(dirname "$0")/common.sh"
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="focuspix"
STAGE_DIR="$ROOT/build/$APP_NAME"
BOARD_APP_DIR="/home/arduino/ArduinoApps/$APP_NAME"
FQBN="arduino:zephyr:unoq"

find_adb() {
    if [ -n "${ADB:-}" ] && command -v "$ADB" >/dev/null 2>&1; then
        echo "$ADB"
        return 0
    fi
    if [ -x "$HOME/Library/Arduino15/packages/arduino/tools/adb/32.0.0/adb" ]; then
        echo "$HOME/Library/Arduino15/packages/arduino/tools/adb/32.0.0/adb"
        return 0
    fi
    if command -v adb >/dev/null 2>&1; then
        command -v adb
        return 0
    fi
    echo "adb not found. Install via: brew install android-platform-tools" >&2
    return 1
}

find_serial_port() {
    if [ -n "${PORT:-}" ]; then
        echo "$PORT"
        return 0
    fi
    for p in /dev/cu.usbmodem* /dev/ttyACM* /dev/ttyUSB*; do
        if [ -e "$p" ]; then
            echo "$p"
            return 0
        fi
    done
    echo "No USB serial port found. Set PORT=/dev/cu.usbmodemXXXX" >&2
    return 1
}
