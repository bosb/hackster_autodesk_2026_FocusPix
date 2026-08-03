"""FocusPix - Autodesk Fusion .f3d helper.

The single source of truth for the enclosure is enclosure/config.py, built by
enclosure/generate.py into universal STEP files. This script makes those STEP
files into a native Fusion design (.f3d) for application deliverable (d).

Run inside Fusion (Utilities > Add-Ins > Scripts and Add-Ins > Python):
  1. New Script, paste/load this file.
  2. In `run()`'s script folder set the path to the STEP outputs.
  3. Run; it imports base, board, lid into one design and saves <name>.f3d.

This keeps one CAD source of truth (config.py) and avoids a second,
divergent parametric implementation in Fusion.
"""

from __future__ import annotations

import os
import sys

# Path to the STEP files produced by:  .venv/bin/python enclosure/generate.py
STEP_FILES = [
    "focuspix_base.step",
    "focuspix_assembly.step",
    "focuspix_lid.step",
]


def run(context):
    try:
        import adsk.core as core
        import adsk.fusion as fusion
        app = core.Application.get()
    except Exception as exc:
        raise RuntimeError("This script must run inside Autodesk Fusion.") from exc

    out_dir = os.path.dirname(os.path.abspath(__file__))
    step_dir = os.path.join(os.path.dirname(out_dir), "out")

    docs = app.documents
    new_doc = docs.add(fusion.DesignDocumentType)

    im = new_doc.importManager
    for name in STEP_FILES:
        path = os.path.join(step_dir, name)
        if not os.path.exists(path):
            print(f"skipping missing file: {path}")
            continue
        options = im.createSTEPImportOptions(path)
        im.importToCurrentDocument(options)
        print(f"imported {name}")

    design = fusion.Design.cast(new_doc.products.item(0))
    design.unitsManager.distanceDisplayUnits = fusion.DistanceUnits.MillimeterDistanceUnits

    save_path = os.path.join(out_dir, "FocusPix_enclosure.f3d")
    new_doc.saveAs(save_path, "FocusPix enclosure", "", True)
    print(f"saved {save_path}")
