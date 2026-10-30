"""FocusPix enclosure generator (CadQuery).

Builds the low-profile tray base and lid, a board placeholder, and exports
STEP plus STL - per part and a combined single-print plate
(focuspix_printplate.stl) - for PCBWay / Fusion import. Geometric self-checks
probe every
opening: the matrix window, USB plug notch, Qwiic cable notch, debug slot,
rail slots, header floor slots, vents and the keyring opening must really
be holes.

Usage:
    .venv/bin/python enclosure/generate.py [--outdir enclosure/out]
"""

import argparse
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402


# ---------------------------------------------------------------- helpers


def slot_tool(x1, y1, x2, y2, z0, z1, r=1.0, r_cap=8.0):
    """Rounded-rectangle through-cut tool spanning z0..z1.

    r is the corner fillet radius (falls back to the full-round cap).
    """
    w = x2 - x1
    d = y2 - y1
    dz = z1 - z0
    fil = r if r is not None else r_cap
    return (
        cq.Workplane("XY")
        .box(w, d, dz)
        .edges("|Z")
        .fillet(min(fil, w / 2.0, d / 2.0))
        .translate(((x1 + x2) / 2.0, (y1 + y2) / 2.0, (z0 + z1) / 2.0))
    )


def rounded_box_tool(x1, y1, x2, y2, z0, z1, r):
    """Positive rounded-rect prism spanning x1..x2, y1..y2, z0..z1."""
    return (
        cq.Workplane("XY")
        .box(x2 - x1, y2 - y1, z1 - z0)
        .edges("|Z")
        .fillet(min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
        .translate(((x1 + x2) / 2.0, (y1 + y2) / 2.0, (z0 + z1) / 2.0))
    )


def rect_tool(x1, y1, x2, y2, z0, z1):
    """Plain rectangular cut tool spanning z0..z1."""
    return (
        cq.Workplane("XY")
        .box(x2 - x1, y2 - y1, z1 - z0)
        .translate(((x1 + x2) / 2.0, (y1 + y2) / 2.0, (z0 + z1) / 2.0))
    )


# ---------------------------------------------------------------- builders


def make_base():
    """Tray: walls + floor, press-fit pillars, header slots, USB plug notch,
    Qwiic cable notch."""
    base = (
        cq.Workplane("XY")
        .box(C.OUTER_W, C.OUTER_D, C.RIM_Z)
        .edges("|Z")
        .fillet(C.CORNER_R)
        .translate((C.CX, C.CY, C.RIM_Z / 2.0))
    )

    cavity = (
        cq.Workplane("XY")
        .box(C.INNER_W, C.INNER_D, C.RIM_Z - C.FLOOR_T)
        .edges("|Z")
        .fillet(C.CAVITY_CORNER_R)
        .translate((C.CX, C.CY, (C.FLOOR_T + C.RIM_Z) / 2.0))
    )
    base = base.cut(cavity)

    # press-fit pillars (screwless board + lid retention): rooted in the floor,
    # the board slides down the plain Ø3.0 shaft (no tip flare), press comes
    # from the lid plate's tight bores
    for hx, hy in C.MOUNTING_HOLES:
        root = cq.Solid.makeCone(
            C.PIN_ROOT_D / 2.0, C.PIN_SHAFT_D / 2.0, C.STANDOFF_H,
            cq.Vector(hx, hy, C.FLOOR_T))
        shaft = cq.Solid.makeCylinder(
            C.PIN_SHAFT_D / 2.0,
            C.PIN_TOP_Z - (C.FLOOR_T + C.STANDOFF_H),
            cq.Vector(hx, hy, C.FLOOR_T + C.STANDOFF_H))
        base = base.union(root.fuse(shaft))

    # through-floor slots under the GPIO header housings
    sx = C.HEADER_SLOT_MARGIN_X
    sy = C.HEADER_SLOT_MARGIN_Y
    for hx1, hy1, hx2, hy2 in C.HEADER_HOUSINGS:
        slot = rect_tool(
            hx1 - sx, hy1 - sy, hx2 + sx, hy2 + sy,
            -0.1, C.FLOOR_T + 0.1,
        )
        base = base.cut(slot)

    # USB-C plug notch through the -x wall band
    nx1, ny1, nx2, ny2 = C.USB_MINUS
    base = base.cut(rect_tool(
        nx1, ny1, nx2, ny2,
        C.BOARD_TOP_Z - 2.0, C.LIP_Z_BOT - 0.05,
    ))

    # Qwiic cable notch through the +x wall band (mirrors the USB-C recipe)
    qx1, qy1, qx2, qy2 = C.QWIIC_PLUS
    base = base.cut(rect_tool(
        qx1, qy1, qx2, qy2,
        C.BOARD_TOP_Z - 2.0, C.LIP_Z_BOT - 0.05,
    ))

    # bottom vent stripes: through-floor slots in the BASE_VENT plan
    # (rows along x, three segments per row around the header slot bands)
    vw = C.BASE_VENT_W / 2.0
    for ry in C.BASE_VENT_ROWS:
        for sx1, sx2 in C.BASE_VENT_SEGMENTS:
            base = base.cut(slot_tool(
                sx1, ry - vw, sx2, ry + vw,
                -0.1, C.FLOOR_T + 0.1, r=0.7))

    # external closed keyring loop protruding from the front wall, case-centred
    ox1, oy1, ox2, oy2 = C.LANYARD_LOOP_XY
    lz0, lz1 = C.LANYARD_LOOP_Z
    loop = rounded_box_tool(
        ox1, oy1, ox2, oy2, lz0, lz1, C.LANYARD_LOOP_CORNER_R)
    hx1, hy1, hx2, hy2 = C.LANYARD_LOOP_HOLE
    loop = loop.cut(rounded_box_tool(
        hx1, hy1, hx2, hy2, lz0 - 0.2, lz1 + 0.2, C.LANYARD_HOLE_CORNER_R))
    base = base.union(loop)

    return base


def make_board_placeholder():
    """Slab proxy for collision checks, with the four real Ø3.2 hole cutouts
    so the pillars align without false intersections."""
    board = (
        cq.Workplane("XY")
        .box(C.BOARD_W, C.BOARD_D, C.BOARD_T)
        .translate((C.CX, C.CY, (C.BOARD_BOTTOM_Z + C.BOARD_TOP_Z) / 2.0))
    )
    for hx, hy in C.MOUNTING_HOLES:
        hole = cq.Solid.makeCylinder(
            C.MOUNTING_HOLE_R, C.BOARD_T + 0.2,
            cq.Vector(hx, hy, C.BOARD_BOTTOM_Z - 0.1))
        board = board.cut(hole)
    return board


def make_lid():
    """Plate + cavity-gripping collar band, minus window/tower/rail/LED/vent openings."""
    plate = (
        cq.Workplane("XY")
        .box(C.OUTER_W, C.OUTER_D, C.LID_T)
        .edges("|Z")
        .fillet(C.CORNER_R)
        .translate((C.CX, C.CY, (C.LID_PLATE_Z + C.LID_TOP_Z) / 2.0))
    )
    try:
        plate = plate.edges(">Z").fillet(C.LID_EDGE_R)
    except Exception as exc:  # cosmetic only
        print(f"note: lid top-edge fillet skipped ({exc})")

    # uniform-width collar band: drops into the cavity, grips its faces
    bx = C.INNER_W - 2 * C.LIP_PLUG_CLR
    by = C.INNER_D - 2 * C.LIP_PLUG_CLR
    band = (
        cq.Workplane("XY")
        .box(bx, by, C.LID_TOP_Z - C.LIP_Z_BOT)
        .edges("|Z")
        .fillet(C.CAVITY_CORNER_R - C.LIP_PLUG_CLR)
        .translate((C.CX, C.CY, (C.LIP_Z_BOT + C.LID_TOP_Z) / 2.0))
    )
    band = band.cut(
        cq.Workplane("XY")
        .box(bx - 2 * C.LIP_BAND_W, by - 2 * C.LIP_BAND_W, C.LID_TOP_Z - C.LIP_Z_BOT + 1.0)
        .edges("|Z")
        .fillet(max(0.2, C.CAVITY_CORNER_R - C.LIP_PLUG_CLR - C.LIP_BAND_W))
        .translate((C.CX, C.CY, (C.LIP_Z_BOT + C.LID_TOP_Z) / 2.0))
    )

    lid = plate.union(band)

    # LED matrix window through the plate (and the collar band where it overlaps)
    cut_z0 = C.LIP_Z_BOT - 0.2
    cut_z1 = C.LID_TOP_Z + 0.2
    lid = lid.cut(slot_tool(
        C.WINDOW[0], C.WINDOW[1], C.WINDOW[2], C.WINDOW[3], cut_z0, cut_z1,
        r=C.WINDOW_CORNER_R))

    # JCTL 2x5 debug header tower breaches the plate
    dx1, dy1, dx2, dy2 = C.DEBUG_HEADER
    dm = C.DEBUG_SLOT_MARGIN
    lid = lid.cut(rect_tool(
        dx1 - dm, dy1 - dm, dx2 + dm, dy2 + dm, cut_z0, cut_z1))

    # JSPI 2x3 shrouded header tower breaches the plate
    sx1, sy1, sx2, sy2 = C.SPI_HEADER
    sm = C.SPI_SLOT_MARGIN
    lid = lid.cut(rect_tool(
        sx1 - sm, sy1 - sm, sx2 + sm, sy2 + sm, cut_z0, cut_z1))

    # edge rail slots through the plate (per-rail margins)
    for (rail, margins) in zip(C.EDGE_RAILS, C.RAIL_SLOT_MARGINS):
        rx1, ry1, rx2, ry2 = rail
        mx1, my1, mx2, my2 = margins
        lid = lid.cut(rect_tool(
            rx1 - mx1, ry1 - my1, rx2 + mx2, ry2 + my2, cut_z0, cut_z1))

    # discrete LEDs (power + 4x RGB): one small rounded window each
    for lx1, ly1, lx2, ly2 in C.LED_WINDOWS:
        lid = lid.cut(slot_tool(lx1, ly1, lx2, ly2, cut_z0, cut_z1,
                                r=C.LED_WINDOW_CORNER_R))

    # vent slots through the plate
    for vx, vy in C.LID_VENTS:
        lid = lid.cut(rect_tool(
            vx - C.VENT_LEN / 2.0, vy - C.VENT_W / 2.0,
            vx + C.VENT_LEN / 2.0, vy + C.VENT_W / 2.0, cut_z0, cut_z1))

    # coned blind bores for the base pillars (pure press fit, no snap)
    for hx, hy in C.MOUNTING_HOLES:
        mouth = cq.Solid.makeCone(
            C.LID_PIN_MOUTH_D / 2.0, C.LID_PIN_BORE_D / 2.0,
            C.LID_PIN_CONE_TOP_Z - C.LID_PLATE_Z,
            cq.Vector(hx, hy, C.LID_PLATE_Z))
        bore = cq.Solid.makeCylinder(
            C.LID_PIN_BORE_D / 2.0,
            C.LID_PIN_BLIND_Z - C.LID_PIN_CONE_TOP_Z,
            cq.Vector(hx, hy, C.LID_PIN_CONE_TOP_Z))
        lid = lid.cut(mouth.fuse(bore))

    # power-button press lever: the plate itself at full thickness stays as the
    # lever, fused along its south edge only (hinge crease y = PADDLE y1; the
    # plate is continuous south of it), with a press pad under the far north
    # tip reaching down to the JBTN1 can top so the switch is touched at rest
    px1, py1, px2, py2 = C.PADDLE
    pcx, pcy = C.PADDLE_PAD_CXY
    lid = lid.union(cq.Solid.makeCylinder(
        C.PADDLE_PAD_D / 2.0,
        C.LID_PLATE_Z + 0.15 - C.PADDLE_PAD_BOT_Z,
        cq.Vector(pcx, pcy, C.PADDLE_PAD_BOT_Z)))

    # through slits that free the lever on west, east and north (the south
    # hinge edge stays fused); they cut the whole plate depth and nick the
    # collar band exactly like every other lid opening
    sw = C.PADDLE_SLIT_W
    slit_z = (C.LIP_Z_BOT - 0.2, C.LID_TOP_Z + 0.25)
    for s in (
        (px1 - sw, py1, px1, py2 + sw),                 # west slit
        (px2, py1, px2 + sw, py2 + sw),                 # east slit
        (px1 - sw, py2, px2 + sw, py2 + sw),            # north tip slit
    ):
        lid = lid.cut(slot_tool(*s, slit_z[0], slit_z[1], r=0.5))

    # engraved project title into the plate top face (the lid's print-bed side)
    lid = lid.cut(make_lid_title_tool())

    return lid


def make_lid_title_tool():
    """Title engraving tool standing on the plate top face, extruded down."""
    tx, ty = C.LID_TITLE_CXY
    return cq.Workplane("XY", origin=(tx, ty, C.LID_TOP_Z)).text(
        C.LID_TITLE, C.LID_TITLE_H, -C.LID_TITLE_DEPTH,
        font=C.LID_TITLE_FONT, kind=C.LID_TITLE_KIND,
        halign="center", valign="center")


# ---------------------------------------------------------------- self-checks


def volume_of(shape):
    return shape.val().Volume()


def check_through_hole(part, name, cx, cy, z, size, expect_hole=True):
    """Probe a thin box: it should be either fully inside material or air."""
    probe = (
        cq.Workplane("XY")
        .box(*size)
        .translate((cx, cy, z))
    )
    inter = part.intersect(probe).val().Volume()
    filled = abs(inter - size[0] * size[1] * size[2]) < 1e-6
    if expect_hole:
        ok = inter < 1e-6
    else:
        ok = filled
    print(f"  [{name}] probe volume {inter:.2f} mm^3 -> "
          f"{'hole confirmed' if ok else 'FAIL'}")
    return ok


def verify(bottom, top, board):
    print("geometry self-checks:")
    ok = True
    pz = C.LID_PLATE_Z + C.LID_T / 2.0  # mid-plate

    ok &= check_through_hole(
        top, "LED matrix window", C.WINDOW_CX, C.WINDOW_CY, pz,
        (6.0, 6.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "matrix window rear-right corner",
        C.WINDOW[2] - 1.2, C.WINDOW[3] - 1.2, pz,
        (1.5, 1.5, 0.8), expect_hole=True)
    ok &= check_through_hole(
        top, "JCTL debug slot",
        (C.DEBUG_HEADER[0] + C.DEBUG_HEADER[2]) / 2.0,
        (C.DEBUG_HEADER[1] + C.DEBUG_HEADER[3]) / 2.0, pz,
        (6.0, 2.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "JSPI tower slot",
        (C.SPI_HEADER[0] + C.SPI_HEADER[2]) / 2.0,
        (C.SPI_HEADER[1] + C.SPI_HEADER[3]) / 2.0, pz,
        (3.0, 3.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "web between JSPI slot and lid pin bore #3",
        C.MOUNTING_HOLES[2][0], (32.46 + 33.91) / 2.0, pz,
        (1.2, 0.6, 1.0), expect_hole=False)
    ok &= check_through_hole(
        top, "web between lid pin bore #3 and RGB LED row",
        C.MOUNTING_HOLES[2][0], (37.21 + 41.21) / 2.0, pz,
        (1.2, 1.0, 1.0), expect_hole=False)
    ok &= check_through_hole(
        top, "web between lid pin bore #4 and front rail slot",
        (16.89 + 17.29) / 2.0, 50.80, pz,
        (0.3, 2.0, 1.0), expect_hole=False)
    ok &= check_through_hole(
        top, "front rail slot", 40.0, (C.EDGE_RAILS[0][1] + C.EDGE_RAILS[0][3]) / 2.0,
        pz, (10.0, 1.5, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "back rail slot", 40.0, (C.EDGE_RAILS[1][1] + C.EDGE_RAILS[1][3]) / 2.0,
        pz, (10.0, 1.5, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "power LED window", 2.30, 31.20, pz,
        (1.0, 0.5, 0.8), expect_hole=True)
    for i, (lx1, ly1, lx2, ly2) in enumerate(C.LED_WINDOWS[1:], start=1):
        ok &= check_through_hole(
            top, f"RGB LED window #{i}",
            (lx1 + lx2) / 2.0, (ly1 + ly2) / 2.0, pz,
            (0.8, 0.8, 0.8), expect_hole=True)
    lz0, lz1 = C.LANYARD_LOOP_Z
    lc = (lz0 + lz1) / 2.0
    ok &= check_through_hole(
        bottom, "keyring opening",
        (C.LANYARD_LOOP_HOLE[0] + C.LANYARD_LOOP_HOLE[2]) / 2.0,
        (C.LANYARD_LOOP_HOLE[1] + C.LANYARD_LOOP_HOLE[3]) / 2.0, lc,
        (3.0, 3.6, 1.0), expect_hole=True)
    ok &= check_through_hole(
        bottom, "keyring closed border (material)",
        (C.LANYARD_LOOP_XY[0] + C.LANYARD_LOOP_HOLE[0]) / 2.0,
        (C.LANYARD_LOOP_HOLE[1] + C.LANYARD_LOOP_HOLE[3]) / 2.0, lc,
        (1.4, 2.0, 0.8), expect_hole=False)
    ok &= check_through_hole(
        bottom, "keyring outer border (material)",
        (C.LANYARD_LOOP_HOLE[0] + C.LANYARD_LOOP_HOLE[2]) / 2.0,
        (C.LANYARD_LOOP_HOLE[3] + C.LANYARD_LOOP_XY[3]) / 2.0, lc,
        (3.0, 1.2, 0.8), expect_hole=False)
    ok &= check_through_hole(
        bottom, "keyring border right (material)",
        (C.LANYARD_LOOP_HOLE[2] + C.LANYARD_LOOP_XY[2]) / 2.0,
        (C.LANYARD_LOOP_HOLE[1] + C.LANYARD_LOOP_HOLE[3]) / 2.0, lc,
        (1.4, 2.0, 0.8), expect_hole=False)

    sgc = (C.BASE_VENT_SEGMENTS[1][0] + C.BASE_VENT_SEGMENTS[1][1]) / 2.0
    vr0 = C.BASE_VENT_ROWS[0]
    ok &= check_through_hole(
        bottom, "base vent slot mid (air)",
        sgc, C.BASE_VENT_ROWS[1], C.FLOOR_T / 2.0,
        (1.4, 1.0, 0.8), expect_hole=True)
    ok &= check_through_hole(
        bottom, "base vent web between rows (material)",
        sgc, (C.BASE_VENT_ROWS[1] + C.BASE_VENT_ROWS[2]) / 2.0,
        C.FLOOR_T / 2.0,
        (1.4, 1.4, 0.8), expect_hole=False)
    ok &= check_through_hole(
        bottom, "base vent row margin below row 1 (material)",
        sgc, vr0 - C.BASE_VENT_W / 2.0 - 0.9, C.FLOOR_T / 2.0,
        (1.4, 1.2, 0.8), expect_hole=False)
    ok &= check_through_hole(
        bottom, "base vent west segment (air)",
        (C.BASE_VENT_SEGMENTS[0][0] + C.BASE_VENT_SEGMENTS[0][1]) / 2.0,
        vr0, C.FLOOR_T / 2.0, (1.2, 1.0, 0.8), expect_hole=True)
    ok &= check_through_hole(
        bottom, "base vent east segment (air)",
        (C.BASE_VENT_SEGMENTS[2][0] + C.BASE_VENT_SEGMENTS[2][1]) / 2.0,
        vr0, C.FLOOR_T / 2.0, (1.2, 1.0, 0.8), expect_hole=True)
    for vx, vy in C.LID_VENTS:
        ok &= check_through_hole(
            top, f"lid vent @({vx},{vy})", vx, vy, pz,
            (C.VENT_LEN - 2.0, C.VENT_W - 0.7, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "solid plate control", 30.0, 35.0, pz,
        (6.0, 6.0, 1.0), expect_hole=False)

    for i, (hx1, hy1, hx2, hy2) in enumerate(C.HEADER_HOUSINGS):
        ok &= check_through_hole(
            bottom, f"header slot {i + 1} (base)", (hx1 + hx2) / 2.0,
            (hy1 + hy2) / 2.0, C.FLOOR_T / 2.0,
            (2.5, 4.0, 0.8), expect_hole=True)
    ok &= check_through_hole(
        bottom, "USB plug notch (base)", C.USB_NOTCH_CX, C.USB_NOTCH_CY,
        (C.BOARD_TOP_Z - 2.0 + C.LIP_Z_BOT - 0.05) / 2.0,
        (1.2, 7.0, 2.0), expect_hole=True)
    qwc = (C.BOARD_TOP_Z - 2.0 + C.LIP_Z_BOT - 0.05) / 2.0
    ok &= check_through_hole(
        bottom, "Qwiic cable notch (base)", C.QWIIC_NOTCH_CX,
        C.QWIIC_NOTCH_CY, qwc, (1.2, 7.0, 2.0), expect_hole=True)
    ok &= check_through_hole(
        bottom, "Qwiic wall above notch (material)", C.QWIIC_NOTCH_CX,
        C.QWIIC_NOTCH_CY, (C.LIP_Z_BOT - 0.05 + C.RIM_Z) / 2.0,
        (1.2, 1.2, 1.0), expect_hole=False)
    ok &= check_through_hole(
        bottom, "Qwiic wall below notch (material)", C.QWIIC_NOTCH_CX,
        C.QWIIC_NOTCH_CY, (C.FLOOR_T + C.BOARD_TOP_Z - 2.0) / 2.0,
        (1.2, 1.2, 1.2), expect_hole=False)
    ok &= check_through_hole(
        bottom, "Qwiic notch north web (material)", C.QWIIC_NOTCH_CX,
        C.QWIIC_NY2 + 1.0, qwc, (1.2, 1.2, 1.6), expect_hole=False)
    ok &= check_through_hole(
        bottom, "Qwiic notch south web (material)", C.QWIIC_NOTCH_CX,
        C.QWIIC_NY1 - 1.0, qwc, (1.2, 1.2, 1.6), expect_hole=False)
    hx0, hy0 = C.MOUNTING_HOLES[0]
    ok &= check_through_hole(
        bottom, "pin fills board hole [0]", hx0, hy0,
        C.BOARD_BOTTOM_Z + 0.8, (1.9, 1.9, 0.8), expect_hole=False)
    ok &= check_through_hole(
        bottom, "solid floor control", 30.0, 25.5, C.FLOOR_T / 2.0,
        (8.0, 2.4, 1.0), expect_hole=False)
    ok &= check_through_hole(
        bottom, "true 2 mm wall (straight)", -2.0, 25.0, 8.5,
        (1.4, 1.2, 1.0), expect_hole=False)
    ok &= check_through_hole(
        bottom, "true 2 mm wall (corner lozenge)", -1.12, -1.12, 8.5,
        (1.2, 1.2, 1.0), expect_hole=False)
    zband = (C.LIP_Z_BOT + C.LIP_Z_BOT + C.LIP_DEPTH) / 2.0  # mid-collar
    ok &= check_through_hole(
        top, "collar band material (left)", -0.38, 25.0, zband,
        (0.6, 1.2, 1.0), expect_hole=False)
    ok &= check_through_hole(
        top, "collar band material (back)", 34.29, -0.38, zband,
        (1.2, 0.6, 1.0), expect_hole=False)
    ok &= check_through_hole(
        top, "collar band material (corner)", 0.095, 0.095, zband,
        (0.6, 0.6, 1.0), expect_hole=False)

    for i, (bx, by) in enumerate(C.MOUNTING_HOLES):
        ok &= check_through_hole(
            top, f"lid pin bore #{i + 1}", bx, by, 12.8,
            (1.9, 1.9, 1.0), expect_hole=True)

    bx0, by0 = C.MOUNTING_HOLES[0]
    ok &= check_through_hole(
        bottom, "pin shaft clear beyond Ø3.0 (no tip flare)", bx0 + 1.75,
        by0, 12.5, (0.4, 0.4, 0.8), expect_hole=True)

    pcx, pcy = C.PADDLE_PAD_CXY
    px1, py1, px2, py2 = C.PADDLE
    pmx = (px1 + px2) / 2.0
    pmy = (py1 + py2) / 2.0
    ok &= check_through_hole(
        top, "paddle pad material",
        pcx, pcy, (C.LID_PLATE_Z + C.PADDLE_PAD_BOT_Z) / 2.0,
        (1.8, 1.8, 0.5), expect_hole=False)
    ok &= check_through_hole(
        top, "paddle pad lands on JBTN1 at rest (material)",
        pcx, pcy, C.POWER_BTN_TOP_Z + 0.25,
        (2.0, 2.0, 0.4), expect_hole=False)
    ok &= check_through_hole(
        top, "paddle clears JBTN1 beyond the pad (air)",
        C.POWER_BUTTON[2] - 0.6, C.POWER_BUTTON[1] + 1.7,
        C.POWER_BTN_TOP_Z + 0.25,
        (1.0, 1.0, 0.3), expect_hole=True)
    ok &= check_through_hole(
        top, "paddle flush with lid top (material)",
        px1 + 2.0, pcy, C.LID_TOP_Z - 0.4,
        (2.0, 2.0, 0.5), expect_hole=False)
    ok &= check_through_hole(
        top, "paddle west slit (free)",
        px1 - C.PADDLE_SLIT_W / 2.0, pmy, pz,
        (0.6, 2.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "paddle east slit (free)",
        px2 + C.PADDLE_SLIT_W / 2.0, pmy, pz,
        (0.6, 2.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "paddle north tip slit (free)",
        pmx, py2 + C.PADDLE_SLIT_W / 2.0, pz,
        (2.0, 0.6, 1.0), expect_hole=True)
    ok &= check_through_hole(
        top, "paddle hinge root (material)",
        pmx, py1 - 0.3, pz,
        (2.0, 0.5, 1.0), expect_hole=False)
    ok &= check_through_hole(
        top, "tip slit nicks +y collar band (air)",
        pmx, C.PADDLE[3] + C.PADDLE_SLIT_W - 0.11, 11.0,
        (2.0, 0.16, 0.5), expect_hole=True)
    ok &= check_through_hole(
        top, "collar band material (+y outboard of paddle)",
        pmx, 53.7, 11.0,
        (2.0, 1.0, 0.4), expect_hole=False)

    title = make_lid_title_tool()
    tb = title.val().BoundingBox()
    tint = top.intersect(title).val().Volume()
    tvx = sorted({vx for vx, _ in C.LID_VENTS})
    t_lo = tvx[0] + C.VENT_LEN / 2.0
    t_hi = tvx[-1] - C.VENT_LEN / 2.0
    t_ok = (tb.xmin >= t_lo + 1.0 and tb.xmax <= t_hi - 1.0 and
            tb.ymin >= C.WINDOW[3] + 1.0 and
            tb.ymax <= C.DEBUG_HEADER[1] - C.DEBUG_SLOT_MARGIN - 1.0 and
            tb.zmax <= C.LID_TOP_Z + 1e-6 and
            tb.zmin >= C.LID_TOP_Z - C.LID_TITLE_DEPTH - 1e-6 and
            tint < 1e-6)
    print(f"  [lid title engraving] bbox x[{tb.xmin:.2f},{tb.xmax:.2f}] "
          f"y[{tb.ymin:.2f},{tb.ymax:.2f}] carve {tint:.2f} mm^3 -> "
          f"{'OK' if t_ok else 'FAIL'}")
    ok &= t_ok
    ok &= check_through_hole(
        top, "lid title pocket floor (material)",
        C.LID_TITLE_CXY[0], C.LID_TITLE_CXY[1],
        C.LID_TOP_Z - C.LID_TITLE_DEPTH - 0.2,
        (2.0, 2.0, 0.3), expect_hole=False)

    inter_base = board.intersect(bottom).val().Volume()
    inter_lid = board.intersect(top).val().Volume()
    inter_fit = bottom.intersect(top).val().Volume()
    print(f"  [board vs base] intersection {inter_base:.2f} mm^3 -> "
          f"{'clear' if inter_base < 1e-6 else 'FAIL'}")
    print(f"  [board vs lid]  intersection {inter_lid:.2f} mm^3 -> "
          f"{'clear' if inter_lid < 1e-6 else 'FAIL'}")
    print(f"  [base vs lid]   intersection {inter_fit:.2f} mm^3 -> "
          f"{'ok (press interference only)' if inter_fit < 2.0 else 'FAIL (collar clash)'}")
    ok &= inter_base < 1e-6 and inter_lid < 1e-6 and inter_fit < 2.0
    return ok


# ------------------------------------------------------------------ exports


def make_print_plate(bottom, top):
    """Both parts on one print plate: the base stays floor-down in place, the
    lid is flipped (plain/title top face onto the bed, collar up, bores
    opening skyward) and parked beside it PRINT_PLATE_GAP clear. The parts
    fuse nothing - a compound of exactly two solids - so the slicer reads
    two independent islands: in the assembled pose they interpenetrate at
    the pin press and could never print in place."""
    lb = top.val().BoundingBox()
    zmid = (lb.zmin + lb.zmax) / 2.0
    flipped = top.val().mirror("XY", basePointVector=(0, 0, zmid))
    fb = flipped.BoundingBox()
    bb = bottom.val().BoundingBox()
    parked = flipped.translate(cq.Vector(
        (bb.xmax + C.PRINT_PLATE_GAP) - fb.xmin, 0.0, -fb.zmin))
    plate = cq.Workplane(obj=cq.Compound.makeCompound(
        [bottom.val(), parked]))
    plate_lid = cq.Workplane(obj=parked)
    return plate, plate_lid


def export_any(obj, path, **kw):
    """Export STEP or STL, with a direct OCP fallback for STEP."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".step":
        try:
            cq.exporters.export(obj, path, **kw)
        except Exception:
            from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
            from OCP.IFSelect import IFSelect_RetDone
            writer = STEPControl_Writer()
            writer.Transfer(obj.val(), STEPControl_AsIs)
            status = writer.Write(str(path))
            if status != IFSelect_RetDone:
                raise RuntimeError(f"STEP write failed: {status}")
    else:
        cq.exporters.export(obj, path, **kw)
    print(f"  exported {path} ({os.path.getsize(path)} bytes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="enclosure/out")
    ap.add_argument("--skip-stl", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    base = make_base()
    lid = make_lid()
    board = make_board_placeholder()

    print(f"base volume  : {volume_of(base):.0f} mm^3")
    print(f"lid volume   : {volume_of(lid):.0f} mm^3")
    print(f"board volume : {volume_of(board):.0f} mm^3")
    for name, shape in (("base", base), ("lid", lid), ("board", board)):
        bb = shape.val().BoundingBox()
        print(f"  {name:6s} bbox x[{bb.xmin:.2f},{bb.xmax:.2f}] "
              f"y[{bb.ymin:.2f},{bb.ymax:.2f}] z[{bb.zmin:.2f},{bb.zmax:.2f}]")

    ok = verify(base, lid, board)

    # combined print-plate sanity: the two islands must be fully disjoint
    plate, plate_lid = make_print_plate(base, lid)
    p_overlap = base.intersect(plate_lid).val().Volume()
    p_vol_ok = (abs(volume_of(plate)
                    - (volume_of(base) + volume_of(plate_lid))) < 1e-6)
    p_ok = p_overlap < 1e-6 and p_vol_ok
    pbb = plate.val().BoundingBox()
    print(f"  [print plate] island overlap {p_overlap:.2f} mm^3 "
          f"-> {'disjoint' if p_overlap < 1e-6 else 'FAIL'}")
    print(f"  [print plate] bbox x[{pbb.xmin:.2f},{pbb.xmax:.2f}] "
          f"y[{pbb.ymin:.2f},{pbb.ymax:.2f}] "
          f"z[{pbb.zmin:.2f},{pbb.zmax:.2f}] -> "
          f"{'OK' if p_ok else 'FAIL'}")
    ok &= p_ok
    if not ok:
        print("WARNING: some self-checks failed")

    export_any(base, os.path.join(args.outdir, "focuspix_base.step"))
    export_any(lid, os.path.join(args.outdir, "focuspix_lid.step"))
    if not args.skip_stl:
        export_any(base, os.path.join(args.outdir, "focuspix_base.stl"),
                   tolerance=0.05, angularTolerance=0.2)
        export_any(lid, os.path.join(args.outdir, "focuspix_lid.stl"),
                   tolerance=0.05, angularTolerance=0.2)
        export_any(plate, os.path.join(args.outdir, "focuspix_printplate.stl"),
                   tolerance=0.05, angularTolerance=0.2)

    try:
        asm = cq.Assembly()
        asm.add(base, name="base", color=cq.Color(0.85, 0.85, 0.85))
        asm.add(board, name="unoq_board", color=cq.Color(0.15, 0.55, 0.25))
        asm.add(lid, name="lid", color=cq.Color(0.65, 0.80, 0.90))
        asm.save(os.path.join(args.outdir, "focuspix_assembly.step"), exportType="STEP")
        print(f"  exported {args.outdir}/focuspix_assembly.step")
    except Exception as exc:
        print(f"note: assembly export skipped ({exc})")


if __name__ == "__main__":
    main()
