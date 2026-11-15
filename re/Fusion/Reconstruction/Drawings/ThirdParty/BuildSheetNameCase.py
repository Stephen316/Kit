import hashlib
import io
import json
import os
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / "src"))

import BuildVariants

from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing
from convert.formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing

OLD = Path(
    os.environ.get(
        "KIT_DRAWING_SRC",
        "/private/var/folders/b0/tf903gr929v3hkcly_v3dl800000gn/T/KitFusionDrawings/Variants",
    )
)
OUT = Path(os.environ.get("KIT_DRAWING_OUT", str(HERE / "Out"))) / "Variants"
SOURCE = os.environ.get("KIT_SHEET_SOURCE", "D1FreshLayout")
LABEL = os.environ.get("KIT_SHEET_LABEL", "C24SheetName")
NAME = os.environ.get("KIT_SHEET_NAME", "Kit Sheet Renamed")


def source_parts(label):
    with zipfile.ZipFile(io.BytesIO((OLD / f"{label}.f3z").read_bytes())) as archive:
        names = archive.namelist()
        drawing_name = next(name for name in names if name.endswith(".f2d"))
        design_name = next(name for name in names if name.endswith(".f3d"))
        return archive.read(design_name), archive.read(drawing_name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BuildVariants.OUT = OUT
    design, f2d = source_parts(SOURCE)
    drawing = ReadDrawing(f2d, BuildVariants.inflate)
    before = drawing.Sheet
    sheet = SheetLayout(
        ActiveSheet=NAME,
        SheetSize=before.SheetSize,
        Standard=before.Standard,
        Units=before.Units,
        Width=before.Width,
        Height=before.Height,
        HorizontalZones=before.HorizontalZones,
        VerticalZones=before.VerticalZones,
    )
    changed = EmitDrawing(replace(drawing, Sheet=sheet), BuildVariants.compress)
    again = ReadDrawing(changed, BuildVariants.inflate)
    bundle = BuildVariants.opaque_bundle(changed, design, LABEL)
    path = OUT / f"{LABEL}.f3z"
    path.write_bytes(bundle)
    row = {
        "label": LABEL,
        "source": SOURCE,
        "file": path.name,
        "bytes": len(bundle),
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "f2d_bytes": len(changed),
        "f2d_sha256": hashlib.sha256(changed).hexdigest(),
        "name_before": before.ActiveSheet,
        "name_after": again.Sheet.ActiveSheet,
        "sheet_after": [again.Sheet.SheetSize, again.Sheet.Width, again.Sheet.Height],
        "database_unchanged": BuildVariants.database(changed)
        == BuildVariants.database(f2d),
    }
    (OUT / "PlanSheetName.json").write_text(
        json.dumps({"variants": [row]}, indent=1) + "\n"
    )
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
