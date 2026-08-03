# Bill of Materials (BOM)

FocusPix uses **no extra electronics** — every sensing and display element already lives on
the Arduino UNO Q. You add only power (a standard USB power bank + cable) and the 3D-printed
enclosure.

| Qty | Item | Category | Part / Source | Est. cost |
|-----|------|----------|---------------|-----------|
| 1 | Arduino UNO Q (ABX00162) | Main board | Arduino Store | US $42.00 |
| 1 | USB-C power bank (5000 mAh) | Power | Any retailer | US $10.00 |
| 1 | USB-C cable (short / right-angle) | Power | Any retailer | US $2.00 |
| 1 | PLA/PETG filament (≈40 g) | Enclosure | Any 1.75 mm filament | ≈ US $0.80 |
| 0 | Extra electronics | — | none | — |
| 0 | Fasteners | — | none (press-fit lid bosses) | — |

**Total: ≈ US $54.80**, dominated by the UNO Q itself. The power bank keeps the beacon
running standalone in its case for a full work day.

### What the UNO Q already provides (no add-ons)
- **8 × 13 blue LED matrix** (monochrome blue, 104 pixels) — the focus countdown + weather
  display. This is one display, not two: the same 104 pixels render every mode.
- **4 user RGB LEDs** — status lighting (LEDs 1/2 on the MPU side, LEDs 3/4 on the STM32
  side). Focus = green, break = blue, session end = red flash.
- **USB-C port** — power, programming, and serial; the case has a front plug channel for the
  power cable.
- **Wi-Fi** (MPU QRB2210) — live Open-Meteo weather + the Router Bridge RPC link to the STM32.
- **Clock/timers** — Pomodoro timing runs in the onboard Python firmware.

### Print settings (enclosure)
- Layer height 0.2 mm, 2–3 walls, 20% infill.
- No supports required; lid presses into the base via the two bosses.
- STLs: `enclosure/out/focuspix_base.stl`, `enclosure/out/focuspix_lid.stl`.
