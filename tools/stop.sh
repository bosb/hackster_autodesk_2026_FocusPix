#!/bin/sh
# Stop the FocusPix app on the board.
# Usage: ./tools/stop.sh [--ssh [user@host]]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/tools/common.sh"

if [ "${1:-}" = "--ssh" ]; then
    TARGET="${2:-arduino@192.168.1.111}"
    exec ssh -o StrictHostKeyChecking=accept-new "$TARGET" "arduino-app-cli app stop $BOARD_APP_DIR"
fi

ADB="$(find_adb)"
"$ADB" shell "arduino-app-cli app stop $BOARD_APP_DIR"
