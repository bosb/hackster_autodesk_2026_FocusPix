#!/bin/sh
# Fast MCU-only iteration from the host: compile + upload sketch via USB serial.
# Skips the arduino-app-cli container. Uses staged sketch so sketch.yaml applies.
# Usage: PORT=/dev/cu.usbmodemXXXX ./tools/mcu_only.sh [--compile-only]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/tools/common.sh"

COMPILE_ONLY=0
if [ "${1:-}" = "--compile-only" ]; then
    COMPILE_ONLY=1
fi

if [ ! -f "$STAGE_DIR/sketch/sketch.ino" ]; then
    echo "Stage dir missing. Run ./tools/stage.sh first." >&2
    exit 1
fi

echo "==> compile ($FQBN)"
arduino-cli compile -b "$FQBN" "$STAGE_DIR/sketch"

if [ "$COMPILE_ONLY" = "1" ]; then
    echo "COMPILE OK"
    exit 0
fi

PORT="$(find_serial_port)"
echo "==> upload to $PORT"
arduino-cli upload -b "$FQBN" -p "$PORT" "$STAGE_DIR/sketch"
echo "UPLOAD OK. Watch self-test: column sweep -> checkerboard -> RGB blink."
echo "Serial: arduino-cli monitor -p $PORT -c baudrate=115200"
