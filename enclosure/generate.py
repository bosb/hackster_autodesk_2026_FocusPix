"""FocusPix enclosure generator (CadQuery).

Builds the tray base, the lid, and a board placeholder, exports STEP + STL
for PCBWay / Fusion import, and runs geometric self-checks (the matrix window
and the USB-C notch must really be holes).

Usage:
    .venv/bin/python enclosure/generate.py [--outdir enclosure/out]
"""

import argparse
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402


# ---------------------------------------------------------------- builders


def make_base():
    """Tray: floor + walls, standoffs, USB-C notch, vents."""
    base = (
        cq.Workplane("XY")
        .box(C.OUTER_W, C.OUTER_D, C.RIM_Z)
        .edges("|Z")
        .fillet(C.CORNER_R)
        .translate((C.CX, C.CY, C.RIM_Z / 2.0))
    )

    # interior cavity (floor thickness remains at the bottom)
    cavity = (
        cq.Workplane("XY")
        .box(C.INNER_W, C.INNER_D, C.RIM_Z - C.FLOOR_T)
        .translate((C.CX, C.CY, (C.FLOOR_T + C.RIM_Z) / 2.0))
    )
    base = base.cut(cavity)

    # standoffs under the four UNO Q mounting holes + M3 through-holes
    for hx, hy in C.MOUNTING_HOLES:
        boss = (
            cq.Workplane("XY")
            .cylinder(C.STANDOFF_H, C.STANDOFF_D / 2.0)
            .translate((hx, hy, C.FLOOR_T + C.STANDOFF_H / 2.0))
        )
        base = base.union(boss)
        hole = (
            cq.Workplane("XY")
            .cylinder(C.FLOOR_T + C.STANDOFF_H + 0.2, C.STANDOFF_HOLE_D / 2.0)
            .translate((hx, hy, (C.FLOOR_T + C.STANDOFF_H) / 2.0))
        )
        base = base.cut(hole)

    # USB-C plug channel through the front wall
    usb = (
        cq.Workplane("XY")
        .box(C.USB_NOTCH_W, C.WALL_T + 0.2, C.RIM_Z - C.USB_NOTCH_Z_BOTTOM)
        .translate((
            C.USB_NOTCH_CX,
            C.CY + C.OUTER_D / 2.0 - C.WALL_T / 2.0,
            (C.USB_NOTCH_Z_BOTTOM + C.RIM_Z) / 2.0,
        ))
    )
    base = base.cut(usb)

    # vents: left / right walls
    for yc in C.VENT_LEFT:
        slot = (
            cq.Workplane("XY")
            .box(C.WALL_T + 0.2, C.VENT["len"], C.VENT["z_top"] - C.VENT["z_bot"])
            .translate((-C.WALL_T, yc, (C.VENT["z_bot"] + C.VENT["z_top"]) / 2.0))
        )
        base = base.cut(slot)
    for yc in C.VENT_RIGHT:
        slot = (
            cq.Workplane("XY")
            .box(C.WALL_T + 0.2, C.VENT["len"], C.VENT["z_top"] - C.VENT["z_bot"])
            .translate((C.BOARD_W + C.WALL_T, yc, (C.VENT["z_bot"] + C.VENT["z_top"]) / 2.0))
        )
        base = base.cut(slot)
    # vents: back wall
    for xc in C.VENT_BACK:
        slot = (
            cq.Workplane("XY")
            .box(C.VENT["len"], C.WALL_T + 0.2, C.VENT["z_top"] - C.VENT["z_bot"])
            .translate((xc, -C.WALL_T, (C.VENT["z_bot"] + C.VENT["z_top"]) / 2.0))
        )
        base = base.cut(slot)

    return base


def make_board_placeholder():
    return (
        cq.Workplane("XY")
        .box(C.BOARD_W, C.BOARD_D, C.BOARD_T)
        .translate((C.CX, C.CY, (C.BOARD_BOTTOM_Z + C.BOARD_TOP_Z) / 2.0))
    )


def make_lid():
    """Plate + overhanging lip ring + press bosses, minus window/notch."""
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

    # lip ring that hugs the outside of the walls
    ring = (
        cq.Workplane("XY")
        .box(2 * C.LIP_RING_OX, 2 * C.LIP_RING_OY, C.LIP_DEPTH)
        .edges("|Z")
        .fillet(C.CORNER_R)
        .translate((C.CX, C.CY, (C.LIP_Z_BOT + C.LID_PLATE_Z) / 2.0))
    )
    ring_inner = (
        cq.Workplane("XY")
        .box(2 * C.LIP_RING_IX, 2 * C.LIP_RING_IY, C.LIP_DEPTH * 3)
        .translate((C.CX, C.CY, (C.LIP_Z_BOT + C.LID_PLATE_Z) / 2.0))
    )
    ring = ring.cut(ring_inner)

    lid = plate.union(ring)

    # anti-rattle bosses hovering just above the PCB
    for px, py in C.PRESS_BOSSES:
        zbot = C.BOARD_TOP_Z + C.PRESS_GAP
        boss = (
            cq.Workplane("XY")
            .cylinder(C.LID_PLATE_Z - zbot, C.PRESS_BOSS_D / 2.0)
            .translate((px, py, (zbot + C.LID_PLATE_Z) / 2.0))
        )
        lid = lid.union(boss)

    # LED matrix window
    win = (
        cq.Workplane("XY")
        .box(C.WINDOW_W + 0.01, C.WINDOW_H + 0.01, C.LID_T + 1.0)
        .edges("|Z")
        .fillet(C.WINDOW_CORNER_R)
        .translate((C.WINDOW_CX, C.WINDOW_CY, C.LID_PLATE_Z - 0.5))
    )
    lid = lid.cut(win)

    # USB-C notch through the lid (continues the base channel)
    usb_lid = (
        cq.Workplane("XY")
        .box(C.USB_NOTCH_W, 3.6, 5.0)
        .translate((
            C.USB_NOTCH_CX,
            C.CY + C.OUTER_D / 2.0 - 1.7,
            (C.LIP_Z_BOT + C.LID_TOP_Z + 0.5) / 2.0,
        ))
    )
    lid = lid.cut(usb_lid)

    return lid


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


def verify(lid, base):
    print("geometry self-checks:")
    ok = True
    pz = C.LID_PLATE_Z + 0.5  # mid-plate
    ok &= check_through_hole(
        lid, "LED matrix window", C.WINDOW_CX, C.WINDOW_CY, pz,
        (6.0, 6.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        lid, "USB-C notch (lid)", C.USB_NOTCH_CX,
        C.CY + C.OUTER_D / 2.0 - 1.7, pz,
        (6.0, 3.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        base, "USB-C notch (base)", C.USB_NOTCH_CX,
        C.CY + C.OUTER_D / 2.0 - C.WALL_T / 2.0, 16.0,
        (6.0, 3.0, 1.0), expect_hole=True)
    ok &= check_through_hole(
        lid, "solid plate control", 20.0, 20.0, pz,
        (6.0, 6.0, 1.0), expect_hole=False)
    return ok


# ------------------------------------------------------------------ exports


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

    ok = verify(lid, base)
    if not ok:
        print("WARNING: some self-checks failed")

    # fabrication files
    export_any(base, os.path.join(args.outdir, "focuspix_base.step"))
    export_any(lid, os.path.join(args.outdir, "focuspix_lid.step"))
    if not args.skip_stl:
        export_any(base, os.path.join(args.outdir, "focuspix_base.stl"),
                   tolerance=0.05, angularTolerance=0.2)
        export_any(lid, os.path.join(args.outdir, "focuspix_lid.stl"),
                   tolerance=0.05, angularTolerance=0.2)

    # reference assembly (base + board + lid), STEP only
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
