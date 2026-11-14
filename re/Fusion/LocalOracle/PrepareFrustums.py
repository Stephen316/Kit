from datetime import datetime, timezone
import hashlib
import json
from math import hypot, pi
from pathlib import Path
import sys


root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "src"))

from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmb import EmitFrustumSmb
from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmt import EmitFrustumSmt
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


output = Path(__file__).resolve().parent / "Frustums"
output.mkdir(exist_ok=True)
stamp = GeometryStamp("Kit", "Independent analytic frustum", datetime.now(timezone.utc).isoformat())
report = {"scope": "Production frustum generation from dimensions only; no source archive, template or CAD runtime", "cases": []}
for name, bottom, top, height, base in (("Expanding", 10.0, 14.0, 17.0, (20.0, -30.0, 5.0)), ("Shrinking", 14.0, 8.0, 23.0, (-12.0, 7.0, -4.0)), ("CylindricalLimit", 9.0, 9.0, 11.0, (1.0, 2.0, 3.0))):
    model = FrustumBody(bottom, top, height, base)
    denominator = bottom * bottom + bottom * top + top * top
    center_z = base[2] + height * (bottom * bottom + 2 * bottom * top + 3 * top * top) / (4 * denominator)
    radius = max(bottom, top)
    expected = {"volume_cm3": pi * height * denominator / 3000, "area_cm2": pi * ((bottom + top) * hypot(height, top - bottom) + bottom * bottom + top * top) / 100, "center_cm": [base[0] / 10, base[1] / 10, center_z / 10], "min_cm": [(base[0] - radius) / 10, (base[1] - radius) / 10, base[2] / 10], "max_cm": [(base[0] + radius) / 10, (base[1] + radius) / 10, (base[2] + height) / 10]}
    for suffix, emit in (("smt", EmitFrustumSmt), ("smb", EmitFrustumSmb)):
        payload = emit(model, stamp)
        target = output / (name + "." + suffix)
        target.write_bytes(payload)
        report["cases"].append({"name": name, "format": suffix, "file": target.name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "input_mm": {"bottom_radius": bottom, "top_radius": top, "height": height, "base": list(base)}, "expected": expected})
(output / "Preparation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
