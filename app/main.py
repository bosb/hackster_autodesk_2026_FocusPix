"""FocusPix - Pomodoro focus beacon (runs on the Arduino UNO Q, QRB2210).

The MPU (Debian/Python) runs the Pomodoro state machine, fetches the weather
from Open-Meteo (no API key), renders frames for the 8x13 LED matrix and
controls the RGB LEDs. Frames are pushed to the STM32 MCU over the Router
Bridge (firmware/focuspix.ino).

On the board:
    from arduino.app_utils import App, Bridge, Leds
    App.run(user_loop=loop)

Off the board (any Python 3): the same logic runs but renders frames to the
console as ASCII art, so the display code can be developed and tested locally.

Display language
----------------
  focus    : minutes remaining (5x8 digits) + vertical progress bar + live dot
  break    : minutes remaining, blinking
  weather  : weather icon + temperature, shown at the start of each session
             (and whenever the cached reading is older than refresh_minutes)
  flash    : full-matrix flashes when a session completes

Status colours (RGB LED 1 "user" on the MPU, plus MCU RGB LED 3 via Bridge):
  green = focus session, blue = break, red = session just ended.
"""

import json
import math
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from fonts import (  # noqa: E402
    blank,
    frame_to_string,
    set_progress_bar,
    two_digit_frame,
    weather_frame,
)

CONFIG_PATH = os.path.join(HERE, "config.json")

# --------------------------------------------------------------------- board
try:
    from arduino.app_utils import App, Bridge, Leds  # noqa: E402

    ON_BOARD = True
except Exception:  # pragma: no cover - depends on environment
    ON_BOARD = False


class _StubBridge:
    def call(self, method, *args):
        print(f"[bridge] {method}{args if args else ''}")


class _StubLeds:
    def set_led1_color(self, r, g, b):
        print(f"[led1] r={r} g={g} b={b}")

    def set_led2_color(self, r, g, b):
        print(f"[led2] r={r} g={g} b={b}")


if not ON_BOARD:  # pragma: no cover - offline development/test mode
    Bridge, Leds = _StubBridge(), _StubLeds()

# ------------------------------------------------------------ weather config
STATE_FOCUS = "focus"
STATE_BREAK = "break"
PHASE_WEATHER = "weather"
PHASE_RUN = "run"
PHASE_FLASH = "flash"

WMO_ICONS = {
    0: "sun", 1: "sun", 2: "sun", 3: "cloud",
    45: "fog", 48: "fog",
    51: "rain", 53: "rain", 55: "rain", 56: "rain", 57: "rain",
    61: "rain", 63: "rain", 65: "rain", 66: "rain", 67: "rain",
    71: "snow", 73: "snow", 75: "snow", 77: "snow",
    80: "rain", 81: "rain", 82: "rain", 85: "snow", 86: "snow",
    95: "thunder", 96: "thunder", 99: "thunder",
}


def fetch_weather(cfg):
    """Open-Meteo current conditions -> (temp_c, wmo_code) or None."""
    lat = cfg["weather"].get("latitude", 45.4642)
    lon = cfg["weather"].get("longitude", 9.1900)
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code"
        "&forecast_days=1&timezone=auto"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
        cur = data["current"]
        return int(round(cur["temperature_2m"])), int(cur["weather_code"])
    except Exception:
        return None


# --------------------------------------------------------------------- logic
class FocusPix:
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = STATE_FOCUS
        self.sessions_done = 0
        self.weather = None
        self.last_weather_shown = -1e18  # boot: always show the weather first
        self.last_send = 0.0
        self.last_flash = 0.0
        self._start_session(0.0, cfg["focus_minutes"])

    # -- timing helpers --------------------------------------------------
    def _start_session(self, now, minutes):
        self.dur_min = minutes
        self.session_end = now + minutes * 60.0
        refresh = self.cfg["weather"]["refresh_minutes"] * 60.0
        if now - self.last_weather_shown >= refresh:
            self.phase = PHASE_WEATHER
            self.phase_end = now + self.cfg["weather"]["show_seconds"]
            self.last_weather_shown = now
        else:
            self.phase = PHASE_RUN
        self._status(now)

    def _advance(self, now):
        if self.state == STATE_FOCUS:
            self.sessions_done += 1
            self.state = STATE_BREAK
            if self.sessions_done % self.cfg["sessions_before_long_break"] == 0:
                minutes = self.cfg["long_break_minutes"]
            else:
                minutes = self.cfg["short_break_minutes"]
        else:
            self.state = STATE_FOCUS
            minutes = self.cfg["focus_minutes"]
        self._start_session(now, minutes)

    # -- status LEDs -------------------------------------------------------
    def _status(self, now):
        if self.state == STATE_FOCUS:
            r, g, b = 0, 120, 0
        else:
            r, g, b = 0, 0, 120
        if PHASE_FLASH == self.phase and int(now * 2) % 2:
            r, g, b = 120, 0, 0
        try:
            Leds.set_led1_color(r, g, b)
            if ON_BOARD:
                Bridge.call("rgb_set", 3, r, g, b)
        except Exception:
            pass

    # -- main tick ----------------------------------------------------------
    def tick(self, now):
        if self.phase == PHASE_WEATHER:
            if self.weather is None:
                self.weather = fetch_weather(self.cfg)
            if now >= self.phase_end:
                self.phase = PHASE_RUN
                self.last_send = 0.0
                self._status(now)
        elif self.phase == PHASE_RUN:
            if now >= self.session_end:
                self.phase = PHASE_FLASH
                self.phase_end = now + 2.0
                self.last_send = 0.0
        elif self.phase == PHASE_FLASH:
            if now >= self.phase_end:
                self._advance(now)
        self._render(now)

    # -- rendering ------------------------------------------------------------
    def _frame(self, now):
        if self.phase == PHASE_WEATHER:
            if self.weather:
                temp, code = self.weather
                icon = WMO_ICONS.get(code, "cloud")
                temp = max(0, min(99, temp))  # compact digits can't show a sign
                return frame_to_string(weather_frame(str(temp), icon))
            return blank()

        if self.phase == PHASE_FLASH:
            on = int(now * 4) % 2 == 0
            return "1" * 104 if on else "0" * 104

        # PHASE_RUN: countdown
        remaining = max(0.0, self.session_end - now)
        minutes = max(0, int(math.ceil(remaining / 60.0)))
        text = str(min(minutes, 99))

        grid = two_digit_frame(text)
        progress = 1.0 - (remaining / (self.dur_min * 60.0))
        set_progress_bar(grid, max(0.0, min(1.0, progress)))

        if self.state == STATE_BREAK:
            blink = int(now * self.cfg["display"]["blink_hz"]) % 2 == 0
            if not blink:
                return "0" * 104
        else:
            # live dot, bottom-right
            dot = int(now * self.cfg["display"]["blink_hz"]) % 2 == 0
            grid[7][12] = 1 if dot else 0

        return frame_to_string(grid)

    def _render(self, now):
        hz = self.cfg["display"]["frame_refresh_hz"]
        if self.phase == PHASE_RUN and self.state == STATE_BREAK:
            hz = max(hz, self.cfg["display"]["blink_hz"] * 2)
        if self.phase == PHASE_FLASH:
            hz = 4
        if now - self.last_send < 1.0 / hz:
            return
        self.last_send = now

        frame = self._frame(now)
        if not ON_BOARD:
            if frame != getattr(self, "_last_printed", None):
                print("\n" + render_ascii(frame))
                print(f"state={self.state} phase={self.phase} "
                      f"sessions={self.sessions_done} weather={self.weather}")
                self._last_printed = frame
            return
        try:
            Bridge.call("matrix_show", frame)
        except Exception:
            pass


def render_ascii(frame):
    """104-char frame -> readable 8x13 text block (offline preview)."""
    rows = []
    for r in range(8):
        rows.append("".join("#" if c == "1" else "." for c in frame[r * 13:(r + 1) * 13]))
    return "\n".join(rows)


# --------------------------------------------------------------------- entry
def loop():
    app.tick(time.monotonic())


def main():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    globals()["app"] = FocusPix(cfg)
    if ON_BOARD:
        App.run(user_loop=loop)
    else:  # pragma: no cover - offline
        try:
            while True:
                app.tick(time.monotonic())
                time.sleep(0.05)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
