# DEPLOY — FocusPix CLI deploy runbook (no IDE)

Deployed 2026-09-26 to Arduino UNO Q over USB. App `user:focuspix` running.

## Prerequisites

- `arduino-cli 1.4.1`, core `arduino:zephyr:unoq 0.90.0` (FQBN `arduino:zephyr:unoq`)
- Board on USB (`/dev/cu.usbmodem*`, adb id `3969024376`) or Wi-Fi `192.168.1.111`
- `adb`: Arduino15-bundled
  `~/Library/Arduino15/packages/arduino/tools/adb/32.0.0/adb`
  (fallback: `brew install android-platform-tools`)
- `.venv/bin/python` for offline checks

## Scripts (`tools/`)

| Script | Action |
|---|---|
| `verify.sh` | `tests/test_app.py` (7 checks, retries once) + `py_compile` |
| `stage.sh` | Assemble `build/focuspix/` to Arduino App spec |
| `deploy.sh` | `adb push` + `arduino-app-cli app stop/start` + log tail |
| `mcu_only.sh` | Host `arduino-cli compile/upload` via USB serial |
| `logs.sh` / `stop.sh` | Tail logs / stop app (`--ssh` supported) |

`common.sh` resolves `ROOT`, `ADB`, `PORT`, `FQBN`, `STAGE_DIR`,
`BOARD_APP_DIR=/home/arduino/ArduinoApps/focuspix`.

## Layout mapping (`stage.sh`)

```
app/main.py, fonts.py, config.json -> build/focuspix/python/
firmware/focuspix.ino               -> build/focuspix/sketch/sketch.ino
generated: app.yaml, sketch/sketch.yaml, python/requirements.txt
```

`app.yaml`: name FocusPix, no bricks/ports. `sketch.yaml`: profile
`default` with `arduino:zephyr` platform + `Arduino_RouterBridge 0.4.1`
(+ `RPClite 0.2.1`, `ArxContainer 0.7.0`, `ArxTypeTraits 0.3.1`,
`DebugLog 0.8.4`, `MsgPack 0.4.2`). `Arduino_LED_Matrix 0.1.3` is
core-bundled, no entry needed. `requirements.txt` is intentionally empty
(stdlib only; `arduino.app_utils` is preinstalled on the board).

## Deploy sequence

```bash
./tools/verify.sh
./tools/stage.sh
./tools/deploy.sh                 # USB adb path (default)
./tools/deploy.sh --ssh           # fallback: scp/ssh arduino@192.168.1.111
./tools/logs.sh                   # check "App started", no errors
PORT=/dev/cu.usbmodemXXXX ./tools/mcu_only.sh   # MCU-only fast iteration
```

On-board `app start` compiles the sketch via remoteocd, flashes the STM32,
then provisions the Python container (`focuspix-main-1`). First run is slow.
Host compile reference: 80 KB flash (10%), 32 KB RAM (12%).

## Verification on board

- `arduino-app-cli app list | grep focuspix` -> `running`
- `arduino-app-cli app logs ~/ArduinoApps/focuspix` -> `App started`, no traceback
- Matrix: weather frame ~8 s (icon cols 0-4 + temp) -> countdown `MM` +
  progress bar col 12 + live dot; RGB green focus / blue break / red 2 s flash
- On-board logs are quiet by design (ASCII frames print only off-board)

## Troubleshooting

- `Arduino_Helpers.h: No such file` -> include was removed from firmware
  (unused). Do not re-add; it exists in neither the library index nor the core.
- `PIN_PH10 was not declared` -> use `LED3_R/G/B`, `LED4_R/G/B` variant macros
  (`variant.h`), not `PIN_PHxx`.
- `test_one_display_at_a_time` fails with `('weather', '00000')` -> transient
  live Open-Meteo fetch returned `None` (blank frame). Re-run `verify.sh`
  (it retries once); network-dependent, not a code regression.
- `adb not found` -> use the Arduino15 path above or brew package.
- SSH host-key failure -> scripts pass `StrictHostKeyChecking=accept-new`.
- `build/` is git-ignored staging output; `tools/` is committed.
