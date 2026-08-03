"""FocusPix enclosure - parametric configuration.

All dimensions are in millimetres. The coordinate frame matches the official
UNO Q STEP model (board origin at the bottom-left corner of the PCB):

    x  -> 68.58 mm (long edge)
    y  -> 53.34 mm (short edge; USB-C + LED matrix live on the +y "front" edge)
    z  -> up, from the enclosure floor

Board data was verified against:
  - official simplified STEP model (ABX00162)
  - official board-level drill file 48DMVQAD1_SGB-20250729a4-1-8.drl
    (T08 = 3.2 mm non-plated x4  => the four mounting holes)
  - official pinout PDF page 3 (LED matrix 8x13 geometry)
"""

# ---------------------------------------------------------------- UNO Q board
BOARD_W = 68.58            # long edge
BOARD_D = 53.34            # short edge
BOARD_T = 1.6              # PCB thickness (clearance assumption)

# Four mounting holes, centres in board coordinates (drill file, mm).
# They match the classic Arduino UNO R3 pattern (0.1/0.3/1.4/2.0/2.1/2.15 in).
MOUNTING_HOLES = [
    (2.54, 7.62),
    (2.54, 35.56),
    (53.34, 50.80),
    (54.61, 2.54),
]
MOUNTING_HOLE_R = 1.6      # drilled radius (3.2 mm hole)

# LED matrix 8x13: cover solid #120 in the STEP model, cross-checked against
# the pinout page 3 drawing. Window gets a 1 mm safety margin each side.
MATRIX_BBOX = (27.05, 36.88, 41.55, 46.87)     # x1, y1, x2, y2 (board coords)
MATRIX_WINDOW_MARGIN = 1.0
WINDOW_CORNER_R = 1.0

# USB-C receptacle (STEP solid #115): x 12.15..24.85, y 41.92..47.00.
USB_X1, USB_X2 = 11.90, 25.10        # notch width, centred on the receptacle
USB_NOTCH_Z_BOTTOM = 9.0            # plug opening bottom (covers plug shell)

# -------------------------------------------------------------------- tray base
FLOOR_T = 2.0                # floor thickness
WALL_T = 2.0                 # side wall thickness
GAP = 1.0                    # board-to-wall clearance
RIM_Z = 22.0                 # interior height (top of the walls)
STANDOFF_H = 6.0             # board bottom sits this high above the floor
STANDOFF_D = 9.0             # boss diameter
STANDOFF_HOLE_D = 3.4        # optional M3 screw hole through boss + floor

# Board bottom face ends up at z = FLOOR_T + STANDOFF_H = 8.0 mm.
# With a 1.6 mm board the top face sits at 9.6 mm; a ~22 mm interior gives
# ~10 mm headroom above the tallest component (USB-C stack is 9 mm tall).

# ----------------------------------------------------------------------- vents
# Small slots above board level on the left/right/back walls.
VENT = {"len": 10.0, "width": 1.5, "z_bot": 16.0, "z_top": 17.5}
VENT_LEFT = [24.0, 32.0]
VENT_RIGHT = [24.0, 32.0]
VENT_BACK = [20.0, 35.0, 50.0]

# -------------------------------------------------------------------------- lid
LID_T = 3.0                  # top plate thickness
LIP_DEPTH = 1.5              # ring drops this far over the outside of the walls
LIP_T = WALL_T               # ring wall thickness (= hugs the outer wall tops)

# Anti-rattle bosses on the lid underside that hover just above the PCB.
PRESS_BOSSES = [(50.0, 15.0), (18.0, 28.0)]   # board coords, clear of parts
PRESS_BOSS_D = 6.0
PRESS_GAP = 0.2              # gap between boss bottom and board top

# ------------------------------------------------------------------ cosmetics
CORNER_R = 4.0               # outer vertical corner radius
LID_EDGE_R = 1.5             # lid top edge radius

# -------------------------------------------------------------- derived values
_OX1, _OY1 = -WALL_T, -WALL_T
_OX2, _OY2 = BOARD_W + WALL_T, BOARD_D + WALL_T
OUTER_W = _OX2 - _OX1
OUTER_D = _OY2 - _OY1
CX = (_OX1 + _OX2) / 2.0     # enclosure + board centre (board is centred)
CY = (_OY1 + _OY2) / 2.0

INNER_X1, INNER_Y1 = -GAP, -GAP
INNER_X2, INNER_Y2 = BOARD_W + GAP, BOARD_D + GAP
INNER_W = INNER_X2 - INNER_X1
INNER_D = INNER_Y2 - INNER_Y1

BOARD_BOTTOM_Z = FLOOR_T + STANDOFF_H
BOARD_TOP_Z = BOARD_BOTTOM_Z + BOARD_T

LID_PLATE_Z = RIM_Z                    # plate bottom
LID_TOP_Z = RIM_Z + LID_T              # plate top
LIP_Z_BOT = RIM_Z - LIP_DEPTH          # ring bottom

# Ring outer box hugs the outer walls (LIP_T thick), outer half-sizes:
LIP_RING_OX = OUTER_W / 2.0            # x -3 .. 71.58
LIP_RING_OY = OUTER_D / 2.0            # y -3 .. 56.34
# Ring inner cut box sits LIP_T inside the ring outer face:
LIP_RING_IX = LIP_RING_OX - LIP_T
LIP_RING_IY = LIP_RING_OY - LIP_T

# Matrix window (board coords, with margin)
WINDOW = (
    MATRIX_BBOX[0] - MATRIX_WINDOW_MARGIN,
    MATRIX_BBOX[1] - MATRIX_WINDOW_MARGIN,
    MATRIX_BBOX[2] + MATRIX_WINDOW_MARGIN,
    MATRIX_BBOX[3] + MATRIX_WINDOW_MARGIN,
)
WINDOW_CX = (WINDOW[0] + WINDOW[2]) / 2.0
WINDOW_CY = (WINDOW[1] + WINDOW[3]) / 2.0
WINDOW_W = WINDOW[2] - WINDOW[0]
WINDOW_H = WINDOW[3] - WINDOW[1]

USB_NOTCH_CX = (USB_X1 + USB_X2) / 2.0
USB_NOTCH_W = USB_X2 - USB_X1
