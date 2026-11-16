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

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField
from convert.Formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing
from convert.Formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing

OLD = Path(
    os.environ.get(
        "KIT_DRAWING_SRC",
        "/private/var/folders/b0/tf903gr929v3hkcly_v3dl800000gn/T/KitFusionDrawings/Variants",
    )
)
OUT = Path(os.environ.get("KIT_DRAWING_OUT", str(HERE / "Out"))) / "Variants"
SOURCE = os.environ.get("KIT_TYPED_SOURCE", "D1FreshLayout")
LABEL = os.environ.get("KIT_TYPED_LABEL", "C25TypedLayoutA1")
WIDTH = float(os.environ.get("KIT_TYPED_WIDTH", "841.0"))
HEIGHT = float(os.environ.get("KIT_TYPED_HEIGHT", "594.0"))
PAPER = os.environ.get(
    "KIT_TYPED_PAPER", "ISO_full_bleed_A1_(841.00_x_594.00_MM)"
)


def source_parts(label):
    with zipfile.ZipFile(io.BytesIO((OLD / f"{label}.f3z").read_bytes())) as archive:
        names = archive.namelist()
        drawing_name = next(name for name in names if name.endswith(".f2d"))
        design_name = next(name for name in names if name.endswith(".f3d"))
        return archive.read(design_name), archive.read(drawing_name)


def retarget(model):
    objects = []
    changed = 0
    for entry in model.DwgObjects:
        if entry.ClassKind != "LAYOUT":
            objects.append(entry)
            continue
        fields = {field.FieldName: field.FieldValue for field in entry.ClassData.RecordFields}
        if fields.get("PaperWidth") != 420.0:
            objects.append(entry)
            continue
        values = {"PaperWidth": WIDTH, "PaperHeight": HEIGHT, "PaperSize": PAPER}
        record = type(entry.ClassData)(
            tuple(
                DwgField(field.FieldName, values.get(field.FieldName, field.FieldValue))
                for field in entry.ClassData.RecordFields
            )
        )
        objects.append(replace(entry, ClassData=record))
        changed += 1
    return replace(model, DwgObjects=tuple(objects)), changed


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BuildVariants.OUT = OUT
    design, f2d = source_parts(SOURCE)
    drawing = ReadDrawing(f2d, BuildVariants.inflate)
    if drawing.Database is None:
        raise ValueError("source drawing carries no embedded database")
    retargeted, changed = retarget(drawing.Database.Model)
    edited = replace(
        drawing, Database=replace(drawing.Database, Model=retargeted)
    )
    changed_f2d = EmitDrawing(edited, BuildVariants.compress)
    again = ReadDrawing(changed_f2d, BuildVariants.inflate)
    layouts = [
        {field.FieldName: field.FieldValue for field in entry.ClassData.RecordFields}
        for entry in again.Database.Model.DwgObjects
        if entry.ClassKind == "LAYOUT"
    ]
    bundle = BuildVariants.opaque_bundle(changed_f2d, design, LABEL)
    path = OUT / f"{LABEL}.f3z"
    path.write_bytes(bundle)
    row = {
        "label": LABEL,
        "source": SOURCE,
        "file": path.name,
        "bytes": len(bundle),
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "f2d_bytes": len(changed_f2d),
        "f2d_sha256": hashlib.sha256(changed_f2d).hexdigest(),
        "source_f2d_sha256": hashlib.sha256(f2d).hexdigest(),
        "layouts_changed": changed,
        "layouts_after": [
            [layout.get("PaperWidth"), layout.get("PaperHeight"), layout.get("PaperSize")]
            for layout in layouts
        ],
        "projected_objects": len(drawing.Database.Model.DwgObjects),
    }
    (OUT / "PlanTyped.json").write_text(json.dumps({"variants": [row]}, indent=1) + "\n")
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
