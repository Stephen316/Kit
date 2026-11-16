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

from convert.Formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField
from convert.Formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile

OLD = Path(
    os.environ.get(
        "KIT_DRAWING_SRC",
        "/private/var/folders/b0/tf903gr929v3hkcly_v3dl800000gn/T/KitFusionDrawings/Variants",
    )
)
OUT = Path(os.environ.get("KIT_DRAWING_OUT", str(HERE / "Out"))) / "Variants"
SOURCE = os.environ.get("KIT_MOVE_SOURCE", "D1FreshLayout")
LABEL = os.environ.get("KIT_MOVE_LABEL", "C23ViewMove")
DELTA = float(os.environ.get("KIT_MOVE_DELTA", "20.0"))
ORIGIN = (180.46875, 120.609375)


def source_parts(label):
    with zipfile.ZipFile(io.BytesIO((OLD / f"{label}.f3z").read_bytes())) as archive:
        names = archive.namelist()
        drawing_name = next(name for name in names if name.endswith(".f2d"))
        design_name = next(name for name in names if name.endswith(".f3d"))
        return archive.read(design_name), archive.read(drawing_name)


def moved(entry):
    record = type(entry.ClassData)(
        tuple(
            DwgField(
                field.FieldName,
                (ORIGIN[0] + DELTA, ORIGIN[1], 0.0)
                if field.FieldName == "Center"
                else field.FieldValue,
            )
            for field in entry.ClassData.RecordFields
        )
    )
    return replace(entry, ClassData=record)


def retarget(model):
    objects = []
    changed = 0
    for entry in model.DwgObjects:
        if entry.ClassKind == "VIEWPORT":
            fields = {field.FieldName: field.FieldValue for field in entry.ClassData.RecordFields}
            center = fields.get("Center")
            if isinstance(center, tuple) and center[:2] == ORIGIN:
                objects.append(moved(entry))
                changed += 1
                continue
        objects.append(entry)
    return replace(model, DwgObjects=tuple(objects)), changed


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BuildVariants.OUT = OUT
    design, f2d = source_parts(SOURCE)
    model = ReadDwgFile(BuildVariants.database(f2d))
    retargeted, changed = retarget(model)
    data = EmitDwgFile(retargeted)
    again = ReadDwgFile(data)
    centers = [
        {field.FieldName: field.FieldValue for field in entry.ClassData.RecordFields}.get("Center")
        for entry in again.DwgObjects
        if entry.ClassKind == "VIEWPORT"
    ]
    bundle = BuildVariants.opaque_bundle(
        BuildVariants.without_database(f2d, data), design, LABEL
    )
    path = OUT / f"{LABEL}.f3z"
    path.write_bytes(bundle)
    row = {
        "label": LABEL,
        "source": SOURCE,
        "file": path.name,
        "bytes": len(bundle),
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "dwg_bytes": len(data),
        "dwg_sha256": hashlib.sha256(data).hexdigest(),
        "viewports_changed": changed,
        "delta_mm": DELTA,
        "centers_after": [list(center) if isinstance(center, tuple) else center for center in centers],
    }
    (OUT / "PlanMove.json").write_text(json.dumps({"variants": [row]}, indent=1) + "\n")
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
