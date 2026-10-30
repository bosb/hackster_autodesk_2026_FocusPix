#!/bin/sh
# Deploy the staged app to the UNO Q and start it. No IDE.
# Default transport: adb over USB (no password).
# Fallback: ./tools/deploy.sh --ssh [user@host] (default arduino@192.168.1.111)
# Usage: ./tools/deploy.sh [--no-start] [--ssh [target]]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/tools/common.sh"

NO_START=0
SSH_TARGET=""
while [ $# -gt 0 ]; do
    case "$1" in
        --no-start) NO_START=1; shift ;;
        --ssh)
            SSH_TARGET="${2:-arduino@192.168.1.111}"
            if [ "$SSH_TARGET" = "--" ] || [ -z "${2:-}" ]; then
                SSH_TARGET="arduino@192.168.1.111"
            elif [ "${2:-}" != "" ] && [ "$(echo "${2:-}" | cut -c1-2)" != "--" ]; then
                shift
            fi
            shift
            ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

if [ ! -f "$STAGE_DIR/app.yaml" ]; then
    echo "Stage dir missing. Run ./tools/stage.sh first." >&2
    exit 1
fi

if [ -n "$SSH_TARGET" ]; then
    echo "==> scp to $SSH_TARGET:$BOARD_APP_DIR"
    ssh -o StrictHostKeyChecking=accept-new "$SSH_TARGET" "mkdir -p $BOARD_APP_DIR"
    scp -r "$STAGE_DIR/"* "$SSH_TARGET:$BOARD_APP_DIR/"
    if [ "$NO_START" = "0" ]; then
        echo "==> start app"
        ssh -o StrictHostKeyChecking=accept-new "$SSH_TARGET" \
            "arduino-app-cli app stop $BOARD_APP_DIR || true; arduino-app-cli app start $BOARD_APP_DIR"
        echo "==> register as startup app"
        ssh -o StrictHostKeyChecking=accept-new "$SSH_TARGET" "arduino-app-cli properties set default $BOARD_APP_DIR"
        echo "==> logs (tail)"
        ssh -o StrictHostKeyChecking=accept-new "$SSH_TARGET" \
            "arduino-app-cli app logs $BOARD_APP_DIR" | tail -30
    fi
    exit 0
fi

ADB="$(find_adb)"
echo "==> adb push ($ADB)"
"$ADB" wait-for-device
"$ADB" push "$STAGE_DIR" "$BOARD_APP_DIR"

if [ "$NO_START" = "0" ]; then
    echo "==> start app"
    "$ADB" shell "arduino-app-cli app stop $BOARD_APP_DIR || true; arduino-app-cli app start $BOARD_APP_DIR"
    echo "==> register as startup app"
    "$ADB" shell "arduino-app-cli properties set default $BOARD_APP_DIR"
    echo "==> logs (tail)"
    "$ADB" shell "arduino-app-cli app logs $BOARD_APP_DIR" | tail -30
fi

echo "DEPLOY OK: $BOARD_APP_DIR"
