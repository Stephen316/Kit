import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

OUT = Path(os.environ.get("KIT_DESIGN_OUT", str(HERE / "Out"))) / "Designs"
LABEL = os.environ.get("KIT_DESIGN_LABEL", "KitAuthoredCylinder")
RADIUS_MM = float(os.environ.get("KIT_DESIGN_RADIUS", "12.5"))
LENGTH_MM = float(os.environ.get("KIT_DESIGN_LENGTH", "40.0"))
PARAM = os.environ.get("KIT_DESIGN_PARAM", "kitLength")


def Inflate(Packed: bytes, Expected: int) -> bytes:
    from compression import zstd

    Value = zstd.decompress(Packed)
    if len(Value) != Expected:
        raise ValueError("zstd size mismatch")
    return Value


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = DocumentSpec(
        Title=LABEL,
        ParamName=PARAM,
        LengthMm=LENGTH_MM,
        ProfileKind="extrusion",
        RadiusMm=RADIUS_MM,
        ParamComment="Kit authored length",
        SketchName="Kit Sketch",
        ExtrusionName="Kit Extrusion",
        BodyName="Kit Body",
    )
    data = EmitDocument(spec)
    path = OUT / f"{LABEL}.f3d"
    path.write_bytes(data)
    model = ReadDocument(data, Inflate)

    segments = len(model.Segments)
    row = {
        "label": LABEL,
        "file": path.name,
        "bytes": len(data),
        "segments": segments,
        "bodies": len(model.Bodies),
        "materials": len(model.Materials),
        "expected_volume_mm3": 3.141592653589793 * RADIUS_MM * RADIUS_MM * LENGTH_MM,
        "param": PARAM,
        "length_mm": LENGTH_MM,
    }
    (OUT / "DesignPlan.json").write_text(json.dumps(row, indent=1) + "\n")
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
