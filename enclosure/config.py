"""FocusPix enclosure - parametric configuration.

All dimensions are in millimetres. The coordinate frame matches the official
UNO Q STEP model (board origin at the bottom-left corner of the PCB):

    x  -> 68.58 mm (long edge)
    y  -> 53.34 mm (short edge)
    z  -> up, from the enclosure floor

Board data was verified against:
  - official simplified STEP model (ABX00162): per-solid bounding boxes
    (matrix domes, discrete LEDs, USB-C, JCTL, JSPI, rails, header housings;
    the STEP PCB slab has no modeled holes)
  - official datasheet p.37 "Mechanical information" (board 68.58 x 53.34,
    hole pattern follows the UNO form factor; hole dims 13.97 / 15.24 /
    2x 2.54 / 7.62 / 17.78, 4x R1.6) cross-checked against pinout p.1 hole
    rings). NOTE: no drill file exists in reference/; earlier comments
    citing one were an assumption
  - official pinout PDF pages 1 and 3 (cross-check of the 8x13 matrix
    geometry and the four-teal-circle RGB row)

Architecture (2026-10): low-profile two-piece case modelled on the
"Case for Arduino UNO Q" (Thingiverse 7188152, CC BY-NC-ND - referenced for
architecture only, we ship an original design). Board lies component-side up
on short standoffs so the LED matrix faces the lid; tall board parts breach
through lid openings:

  - GPIO header housings poke 5.0 mm below the PCB (STEP solids at
    x 10.18..13.19 and 57.04..60.05, y 7.43..45.93) -> two through-floor
    slots in the base, like the reference case. 4.0 mm standoffs keep their
    tips 0.6 mm above the base bottom so the case still sits flat.
  - USB-C enters from the -x SHORT edge (receptacle 8.94 wide, 3.0 tall,
    overhangs the PCB edge by 0.52). Plug notch through the -x wall only;
    the lid stays solid above the intact wall band.
  - The tall solid at x 12.15..24.84, y 41.92..47.00 (9.0 tall) is the JCTL
    2x5 debug header (12.7 x 5.08), NOT the USB-C; it breaches the lid
    plate through its own slot.
  - The 8.5 mm-tall edge rails (STEP solids #126/#127; pinout p.3 filled bars:
    front x 17.29..65.03, y 49.56..52.06; back x 26.43..65.12, y 1.30..3.80 --
    an unfilled outline at x 8.69..47.39 exists too and was once mis-adopted)
    breach the lid plate via rail slots.
  - The JSPI 2x3 shrouded header tower (STEP solid #115: 5.00 x 7.61, 8.0 tall
    above the PCB top face) also breaches the lid plate via its own slot.
"""

# ---------------------------------------------------------------- UNO Q board
BOARD_W = 68.58            # long edge
BOARD_D = 53.34            # short edge
BOARD_T = 1.6              # PCB thickness (clearance assumption)

# Four mounting holes, centres in board coordinates (mm). Verified against the
# datasheet mechanical drawing p.37 dims ("15.24", "13.97", "2x 2.54", "7.62",
# "17.78") cross-checked with ring deltas and the pinout p.1 hole symbols; the
# STEP PCB slab has no modeled holes, so this drawing is the only CAD source.
# Hole-to-edge pattern: the two USB-end holes sit 13.97/15.24 mm from the -x
# short edge; the opposite pair sits 2.54 mm from the +x short edge.
MOUNTING_HOLES = [
    (13.97, 2.54),
    (66.04, 7.62),
    (66.04, 35.56),
    (15.24, 50.80),
]
MOUNTING_HOLE_R = 1.6      # drilled radius (3.2 mm hole)

# The 104 LED-matrix domes (STEP: 13 columns pitch 2.10 along x, 8 rows pitch
# 2.00 along y; pinout p.3 amber cells match, cells ~1.20 mm). Extents of the
# dome cluster in board coords. The old "matrix cover" solid #115 at
# x 27.05..41.55, y 36.88..46.87 is an unrelated front-centre component that
# was mis-identified as the matrix - do not reuse it.
MATRIX_DOME_ARRAY = (31.41, 4.63, 58.32, 20.32)   # x1, y1, x2, y2 (board coords)

# Lid window over the matrix (board coords). The bottom edge keeps 0.30 mm
# clear of the back-rail slot top (rail 3.80 + margin 0.40 = 4.20) and still
# covers the lowest dome row with 0.13 mm spare.
MATRIX_WINDOW = (30.90, 4.50, 58.80, 20.85)       # 27.9 x 16.35 window
WINDOW_CORNER_R = 1.0

# Real USB-C receptacle (STEP solid): enters from the -x short edge, shell
# 7.9 long (x, plug axis) x 8.94 (y) x 3.0 above the PCB top face, overhanging
# the PCB edge by 0.52 mm.
USB_RECEPTACLE = (-0.52, 33.39, 7.37, 42.33)     # x1, y1, x2, y2 (board coords)
# Plug notch cross-section on the -x wall band. y-range widened for the
# plug shell (8.94) and the cable overmold (~12.7); notch only - the lid
# stays solid above the intact wall band (a plate-level cut there would
# pass nothing).
USB_MINUS = (-3.3, 31.5, -0.95, 44.2)            # x1, y1, x2, y2 (board coords); x1 0.3 past the wall outer face

# JCTL 2x5 debug header tower (STEP solid): 12.7 x 5.08, 9.0 tall above the
# PCB top face - NOT the USB-C. Breaches the lid plate through its own slot.
DEBUG_HEADER = (12.15, 41.92, 24.84, 47.00)      # x1, y1, x2, y2 (board coords)
DEBUG_SLOT_MARGIN = 0.7

# JSPI 2x3 shrouded header tower (STEP solid #115): 5.00 x 7.61, 8.0 tall
# above the PCB top face (case z 7.6..14.6), near the +x edge. Also breaches
# the lid plate through its own slot.
SPI_HEADER = (62.44, 24.15, 67.44, 31.76)        # x1, y1, x2, y2 (board coords)
SPI_SLOT_MARGIN = 0.7

# GPIO header housings (STEP solids #6 / #121): 3.0 mm wide x 38.5 long,
# extending 5.0 mm below the PCB underside.
HEADER_HOUSINGS = [
    (10.18, 7.43, 13.19, 45.93),   # near the left short edge
    (57.04, 7.43, 60.05, 45.93),   # near the right short edge
]
HEADER_SLOT_MARGIN_X = 0.8
HEADER_SLOT_MARGIN_Y = 0.4

# Edge rails for future base boards (STEP solids #126 / #127; the drawing's
# filled connector bars, not the unfilled outline): 2.5 mm wide, 8.5 mm tall
# above the PCB top face. The back bar spans the full LED-matrix length.
EDGE_RAILS = [
    (17.29, 49.56, 65.03, 52.06),  # front rail (+y edge)
    (26.43, 1.30, 65.12, 3.80),    # back rail (-y edge): spans matrix length
]
# Slot margins per rail as (x1, y1, x2, y2) pads.
# Front rail: left pad 0.0 -> the slot starts exactly at the rail end (x 17.29).
# Pin bore #4 (15.24, 50.80, straight bore edge x 16.89) then keeps a 0.40 mm
# web to the slot = one printable line width, so its press ring stays intact.
RAIL_SLOT_MARGINS = [
    (0.0, 0.40, 0.40, 0.40),    # front rail (+y)
    (0.40, 0.40, 0.40, 0.40),   # back rail (-y)
]

# -------------------------------------------------------------------- tray base
FLOOR_T = 1.6                # base floor thickness
WALL_T = 2.0                 # base wall thickness
GAP = 1.0                    # board-to-wall clearance
RIM_Z = 11.6                 # top of the base walls
STANDOFF_H = 4.0             # board bottom sits this high above the floor
                             # (header housing tips stay above the base bottom)

# Screwless retention: four print-in pillars rooted in the floor. The board
# slides down over the PIN as a plain Ø3.0 shaft to its top (NO tip flare -
# a Ø3.5 flare at z 11–13 sat in the board's through-path: Ø3.2 holes could
# never reach their seat). Retention is a pure bore squeeze instead: the lid
# plate's straight bore is 0.1 tight over the shaft (no snap barb).
PIN_ROOT_D      = 5.6        # root Ø at the floor, tapering up to the shaft
PIN_SHAFT_D     = 3.0        # plain shaft through the board holes to the top
PIN_TOP_Z       = 13.0       # pin top, buried inside the lid plate (14.0)
LID_PIN_BORE_D     = 2.9     # straight bore Ø in the plate: 0.1 squeeze over
                             # the Ø3.0 shaft (previously 3.3 with a tip flare)
LID_PIN_MOUTH_D    = 4.0     # lead-in Ø at the plate underside
LID_PIN_CONE_TOP_Z = 12.2    # straight bore starts at this height (case z)
LID_PIN_BLIND_Z    = 13.4    # bore floor, 0.4 below the pin top: no bottoming

# Base floor slots under the GPIO header housings (tails poke below the case).
HEADER_SLOT_T = FLOOR_T + 0.2              # cut tool thickness

# ------------------------------------------------------------------------ lid
LID_T = 2.4                  # lid plate thickness
# Collar band constants live below the derived-values block (band depth/clearance).

# LED matrix window through the lid plate.
# WINDOW = matrix bbox +/- MATRIX_WINDOW_MARGIN (derived below).

# Discrete LEDs (STEP dome solids, board coords):
#   - power LED D27201 (green, 0603 1.6 x 0.8) on the -x edge, just below the
#     USB-C receptacle on the short edge.
#   - four RGB LEDs (D27301/D27302/D27401/D27402) in a 1.91 mm-pitch row near
#     the +x edge (matches the four teal circles on pinout page 1).
POWER_LED_DOME = (1.50, 30.80, 3.10, 31.60)   # x1, y1, x2, y2 (board coords)
RGB_LED_DOMES = [                             # 1.0 x 1.0 dome footprints
    (64.53, 41.66, 65.53, 42.66),
    (64.53, 43.57, 65.53, 44.57),
    (64.53, 45.48, 65.53, 46.48),
    (64.53, 47.38, 65.53, 48.39),
]
LED_WINDOW_MARGIN = 0.45
LED_WINDOW_CORNER_R = 0.6

# Lid vent slots (length along x, width along y), through the plate.
VENT_LEN = 10.0
VENT_W = 1.6
LID_VENTS = [
    (16.0, 24.0), (16.0, 31.0), (16.0, 38.0),
    (54.0, 24.0), (54.0, 31.0), (54.0, 38.0),   # right col x 54: clear of JSPI slot
]

# ------------------------------------------------------------------ cosmetics
CORNER_R = 4.0               # outer vertical corner radius
LID_EDGE_R = 1.5             # lid top edge radius

# -------------------------------------------------------------- derived values
# TRUE 2.0 mm solid walls: outer = cavity + WALL_T. GAP keeps 1.0 mm board
# clearance INSIDE the cavity, so the wall solid is the full WALL_T.
_OX1, _OY1 = -(WALL_T + GAP), -(WALL_T + GAP)
_OX2, _OY2 = BOARD_W + WALL_T + GAP, BOARD_D + WALL_T + GAP
OUTER_W = _OX2 - _OX1
OUTER_D = _OY2 - _OY1
CX = (_OX1 + _OX2) / 2.0     # enclosure + board centre (board is centred)
CY = (_OY1 + _OY2) / 2.0

INNER_X1, INNER_Y1 = -GAP, -GAP
INNER_X2, INNER_Y2 = BOARD_W + GAP, BOARD_D + GAP
INNER_W = INNER_X2 - INNER_X1
INNER_D = INNER_Y2 - INNER_Y1

# Molded keyring loop: closed ring protruding outside the FRONT wall, centred
# on the case x (user moved it there; same 3.0 side / 2.0 outer ring borders
# as the old back-wall design).
LANYARD_LOOP_XY = (CX - 5.2, INNER_Y2, CX + 5.2, INNER_Y2 + 9.8)
                                   # outer plan; y1 flush with the cavity face
                                   # (fused through the full 2.0 wall)
LANYARD_LOOP_HOLE = (CX - 2.2, INNER_Y2 + 2.0, CX + 2.2, INNER_Y2 + 7.8)
                                   # opening, fully beyond the wall band
LANYARD_LOOP_CORNER_R = 1.8
LANYARD_HOLE_CORNER_R = 1.6
LANYARD_LOOP_Z = (2.8, 5.6)                  # ring band height span

# Bottom vent stripes (user: "on the bottom!" - an earlier wall-stripe draft
# was replaced): through-floor slots in the same style as the lid vents, or =
# 1.6 wide, stadium-ended. Three rows run along x; their segments stop short
# of the two GPIO through-floor header slots (BASE_VENT_OBST_MARGIN each
# side), so every row is three segments: west of the west housing, between
# the housings, east of the east housing. Row y positions dodge the four
# pillar root circles (root Ø5.6 + BASE_VENT_PILLAR_MARGIN). Slots are
# through the floor slab: the base prints floor-down, so nothing bridges.
# While the case sits flat the bottom slots still exchange the under-board
# air through the open side gap; hung on the lanyard they vent directly.
BASE_VENT_W = 1.6             # slot width (= lid VENT_W)
BASE_VENT_ROWS = (15.0, 22.0, 29.0)      # row centre y (board coords);
                                         # pitch 7.0 like the lid vent rows
BASE_VENT_EDGE_MARGIN = 2.0   # cavity face -> slot end
BASE_VENT_OBST_MARGIN = 1.5   # GPIO header-slot band -> segment end
BASE_VENT_PILLAR_MARGIN = 1.2 # pillar root circle -> row band (verify checks
                              # it: row bands y 14.2..29.8 vs root circles
                              # clear >= 3.78 / 1.76)

_hb = [(h[0] - HEADER_SLOT_MARGIN_X - BASE_VENT_OBST_MARGIN,
        h[2] + HEADER_SLOT_MARGIN_X + BASE_VENT_OBST_MARGIN)
       for h in HEADER_HOUSINGS]
BASE_VENT_SEGMENTS = [
    (INNER_X1 + BASE_VENT_EDGE_MARGIN, _hb[0][0]),   # west of housing 1
    (_hb[0][1], _hb[1][0]),                          # between the housings
    (_hb[1][1], INNER_X2 - BASE_VENT_EDGE_MARGIN),   # east of housing 2
]

# Concentric cavity corner fillet -> the wall band is WALL_T wide everywhere,
# including around the corners (no fat wedges).
CAVITY_CORNER_R = CORNER_R - WALL_T

BOARD_BOTTOM_Z = FLOOR_T + STANDOFF_H
BOARD_TOP_Z = BOARD_BOTTOM_Z + BOARD_T

LID_PLATE_Z = RIM_Z                    # plate bottom = top of the base walls
LID_TOP_Z = RIM_Z + LID_T              # plate top
# Collar: a narrow band that drops into the cavity and grips its walls.
# Depth 1.2 keeps the band bottom (10.4) above the USB-C receptacle top
# (10.2) and above the Qwiic SH-4 receptacle (also 10.2); clearance gives
# the press fit.
LIP_DEPTH = 1.2              # band drop below the plate
LIP_Z_BOT = LID_PLATE_Z - LIP_DEPTH          # 10.4
LIP_PLUG_CLR = 0.12          # per-side clearance to the cavity faces
LIP_BAND_W = 1.2             # band width (uniform around the corners)

# Power-button press lever: JBTN1 (reboot) = the 6.20 x 6.40 x 2.10 can at
# x 2.74..8.94, y 46.21..52.61 (STEP solid, plunger on the can top; modeled can
# top z 9.3) right past the USB-C on the -x short edge, 0.41 mm shy of the front
# collar band's inner face (53.02). A cantilever LEVER cut from the plate itself
# at full plate thickness (never thinned), fused to the plate along its SOUTH
# edge only (hinge crease y 36.0, the plate is continuous south of it) and free
# on the other three sides through 1.2-wide slits; the long body reaches south
# through the empty plate over the USB-C (shell top z 10.2 stays 1.4 under the
# lever) so the JBTN1 pad sits at the lever's FAR (north) tip - pin on the end
# of the lever, not the middle. No recess, the lever rides flush with the lid
# top; the pad lands exactly on the modeled can top at rest, so the switch is
# already slightly touched in normal position (dead travel 0). Tip press ~3 N
# on PLA (cantilever 13.4 mm crease-to-pad); the east slit ends 1.65 clear of
# the JCTL debug header slot and the tip slit nicks the +y collar band like
# every other lid opening.
POWER_BUTTON = (2.74, 46.21, 8.94, 52.61)      # JBTN1 can plan, board coords
POWER_BTN_TOP_Z = BOARD_TOP_Z + 2.1            # 9.3 case z (modeled can top)
PADDLE = (3.0, 36.0, 8.6, 52.0)                # lever plan; hinge on the -y edge
PADDLE_T = LID_T              # full plate thickness (the lever is the plate)
PADDLE_SLIT_W = 1.2           # through-slit width around the free sides
PADDLE_PAD_D = 3.4            # press pad Ø, fused under the lever tip
PADDLE_PAD_CXY = (5.84, 49.41)                  # pad centre (board coords)
PADDLE_PAD_BOT_Z = POWER_BTN_TOP_Z              # rest: pad touches the can top

# Lid title: "FocusPix" engraved into the print-bed-facing plate top face,
# centred on the lid - the band between the two vent columns (x 21.0/49.0) and
# above the matrix window / below the debug slot is the widest fully solid
# span. Negative-distance text extrudes down: shallow pockets in the bed plane
# print with no bridging. Measured bbox 23.3 x 4.7 mm,
# >= 1.6 mm clear of every neighbour.
LID_TITLE = "FocusPix"
LID_TITLE_FONT = "Arial Narrow"
LID_TITLE_KIND = "bold"
LID_TITLE_H = 6.5             # fontsize (mm)
LID_TITLE_DEPTH = 0.5         # engrave depth into the plate top face
LID_TITLE_CXY = (CX, CY)      # lid centre (34.29, 26.67)

# Matrix window (board coords)
WINDOW = MATRIX_WINDOW
WINDOW_CX = (WINDOW[0] + WINDOW[2]) / 2.0
WINDOW_CY = (WINDOW[1] + WINDOW[3]) / 2.0
WINDOW_W = WINDOW[2] - WINDOW[0]
WINDOW_H = WINDOW[3] - WINDOW[1]

# One small rounded window per discrete LED (power LED first, then RGB 1..4).
_m = LED_WINDOW_MARGIN
LED_WINDOWS = [
    (POWER_LED_DOME[0] - _m, POWER_LED_DOME[1] - _m,
     POWER_LED_DOME[2] + _m, POWER_LED_DOME[3] + _m),
] + [
    (b[0] - _m, b[1] - _m, b[2] + _m, b[3] + _m) for b in RGB_LED_DOMES
]

USB_NX1, USB_NY1, USB_NX2, USB_NY2 = USB_MINUS
USB_NOTCH_CX = (USB_NX1 + USB_NX2) / 2.0
USB_NOTCH_CY = (USB_NY1 + USB_NY2) / 2.0

# Qwiic (QWIIC1, JST SH-4): 4 pins along y, mating face on the +x side, the
# housing 0.52 mm from the board's +x edge -> the cable exits the +x wall,
# diagonally opposite the USB-C (user-confirmed placement). Plan from the
# official STEP model (what the notes first mis-dismissed as a decoy button:
# 4.25 x 6.01 footprint, housing ON the board: z 7.2..10.2 - top equals the
# USB-C shell top). The side notch mirrors the USB_MINUS recipe exactly
# (notch plan 0.05 into the cavity face / 0.3 past the outer face, same z
# band); QWIIC_MOLD_MARGIN covers the SH cable boot around the ~4.8-wide
# plug. The base notch is the whole opening: the lid plate edge band over
# the +x wall stays solid (the intact wall band above the notch closes the
# passage, so a lid-level cut would pass nothing).
QWIIC_CONNECTOR = (63.81, 11.35, 68.06, 17.36)      # SH-4 plan, board coords
QWIIC_MOLD_MARGIN = 1.5       # wall-span margin around the plug/boot
QWIIC_PLUS = (INNER_X2 - 0.05, QWIIC_CONNECTOR[1] - QWIIC_MOLD_MARGIN,
              _OX2 + 0.3, QWIIC_CONNECTOR[3] + QWIIC_MOLD_MARGIN)
QWIIC_NX1, QWIIC_NY1, QWIIC_NX2, QWIIC_NY2 = QWIIC_PLUS
QWIIC_NOTCH_CX = (QWIIC_NX1 + QWIIC_NX2) / 2.0
QWIIC_NOTCH_CY = (QWIIC_NY1 + QWIIC_NY2) / 2.0

# Combined single-print export (`focuspix_printplate.stl`): both parts on one
# plate. They can never print in the assembled pose (the pin press is a
# designed 1.53 mm^3 interference), so each island gets its own print
# orientation: the base stays as modeled (floor on the bed, z 0), the lid is
# mirrored about its own bbox mid-plane and dropped onto z 0 - the plain/
# title top face lands on the bed (solo-lid bed face, title engrave = bed
# texture), collar + bore mouths up - parked to the +x side of the base.
PRINT_PLATE_GAP = 5.0         # spacing between the two plate islands
