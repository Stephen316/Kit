import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
repository = root.parents[2]
sys.path.insert(0, str(repository / "src"))

from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.EmitCylinderSmt import EmitCylinderSmt


model = CylinderBody(15.0, 11.0, (20.0, -30.0, 5.0))
stamp = GeometryStamp("Kit", "Independent analytic cylinder", "Thu Nov 12 00:00:00 2026")
data = EmitCylinderSmt(model, stamp)
output = root / "Brep" / "kit_production_cylinder.smt"
output.write_bytes(data)
report = {"producer": "convert.formats.Fusion.GeometryCodec.EmitCylinderSmt", "output": output.name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "model": {"radius_mm": model.Radius, "height_mm": model.Height, "base_mm": model.BasePoint}, "source_payload_dependencies": [], "scope": "Independent text SMT body, no feature history or F3D document generation"}
output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
