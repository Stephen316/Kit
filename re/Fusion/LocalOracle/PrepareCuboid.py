import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
repository = root.parents[2]
sys.path.insert(0, str(repository / "src"))

from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.EmitCuboidSmb import EmitCuboidSmb
from convert.formats.Fusion.GeometryCodec.Prism.EmitCuboidSmt import EmitCuboidSmt


model = CuboidBody(17.0, 23.0, 31.0, (-7.0, 13.0, 5.0))
stamp = GeometryStamp("Kit", "Independent rectangular cuboid", "2026-11-12T00:00:00Z")
output = root / "Brep"
output.mkdir(exist_ok=True)
report = {
    "purpose": "Independently authored standalone cuboid for parent-coordinated native acceptance",
    "source_payload_dependencies": [],
    "dimensions_mm": [model.Width, model.Depth, model.Height],
    "base_mm": model.BasePoint,
    "expected_volume_cm3": model.Width * model.Depth * model.Height / 1000,
    "expected_bbox_mm": [model.BasePoint, tuple(base + length for base, length in zip(model.BasePoint, (model.Width, model.Depth, model.Height)))],
    "expected_center_mm": tuple(base + length / 2 for base, length in zip(model.BasePoint, (model.Width, model.Depth, model.Height))),
    "expected_topology": {"bodies": 1, "faces": 6, "edges": 12, "vertices": 8},
    "curve_parameterization": "C(u)=start+u*(end-start), edges bounded at u=0 and u=1",
    "outputs": [],
}
for extension, emitter in (("smt", EmitCuboidSmt), ("smb", EmitCuboidSmb)):
    payload = emitter(model, stamp)
    target = output / ("kit_production_cuboid." + extension)
    target.write_bytes(payload)
    report["outputs"].append({"file": target.name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "producer": emitter.__module__})
(output / "ProductionCuboidPreparation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
