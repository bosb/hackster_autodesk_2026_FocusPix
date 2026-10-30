#!/bin/sh
# Assemble the Arduino App folder consumed by arduino-app-cli on the UNO Q.
# Maps repo layout -> App spec layout, generates manifests.
# Usage: ./tools/stage.sh
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/tools/common.sh"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/python" "$STAGE_DIR/sketch"

cp "$ROOT/app/main.py" "$ROOT/app/fonts.py" "$ROOT/app/config.json" "$STAGE_DIR/python/"

cp "$ROOT/firmware/focuspix.ino" "$STAGE_DIR/sketch/sketch.ino"

cat > "$STAGE_DIR/app.yaml" <<'EOF'
name: FocusPix
description: Portable Pomodoro focus beacon with live weather
icon: ⏱️
ports: []
bricks: []
EOF

cat > "$STAGE_DIR/sketch/sketch.yaml" <<'EOF'
profiles:
  default:
    platforms:
      - platform: arduino:zephyr
    libraries:
      - Arduino_RouterBridge (0.4.1)
      - dependency: Arduino_RPClite (0.2.1)
      - dependency: ArxContainer (0.7.0)
      - dependency: ArxTypeTraits (0.3.1)
      - dependency: DebugLog (0.8.4)
      - dependency: MsgPack (0.4.2)
default_profile: default
EOF

cat > "$STAGE_DIR/python/requirements.txt" <<'EOF'
# FocusPix MPU app uses stdlib only (json, math, os, sys, time, urllib).
# arduino.app_utils is preinstalled on the UNO Q, no pip deps required.
EOF

echo "Staged: $STAGE_DIR"
find "$STAGE_DIR" -type f | sort
