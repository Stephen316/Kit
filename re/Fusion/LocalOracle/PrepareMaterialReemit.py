from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "src"))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue


output = Path(__file__).resolve().parent / "RectangleAuthoring"
source = output / "ProductionCuboid.f3d"
payload = source.read_bytes()
model = ReadDocument(payload)
if len(model.Materials) != 1:
    raise RuntimeError("Expected one independently authored material package")
reemitted = EmitParsed(model)
(output / "ProductionCuboidReemitted.f3d").write_bytes(reemitted)
package = model.Materials[0].Package
changed = 0
assets = []
for asset in package.Assets:
    properties = []
    for value in asset.Properties:
        if value.FieldName in ("structural_Density", "thermal_Density"):
            if not isinstance(value.Value, UnitValue):
                raise RuntimeError("Density is not a typed unit value")
            value = replace(value, Value=replace(value.Value, Magnitude=2870.0))
            changed += 1
        properties.append(value)
    assets.append(replace(asset, Properties=tuple(properties)))
if changed != 2:
    raise RuntimeError("Expected structural and thermal density fields")
edited_package = replace(package, Assets=tuple(assets))
edited = replace(model, Materials=(replace(model.Materials[0], Package=edited_package),))
edited_bytes = EmitParsed(edited)
(output / "ProductionCuboidEditedMaterial.f3d").write_bytes(edited_bytes)
report = {
    "scope": "Complete production document read/re-emission and a semantic edit of two typed material density fields; no retained entity or BRep payload blocks",
    "source_sha256": hashlib.sha256(payload).hexdigest(),
    "reemitted_sha256": hashlib.sha256(reemitted).hexdigest(),
    "byte_exact": reemitted == payload,
    "edited_sha256": hashlib.sha256(edited_bytes).hexdigest(),
    "segments": len(model.Segments),
    "entity_records": sum(len(segment.Records) for segment in model.Segments),
    "body_histories": len(model.Bodies),
    "material_packages": len(model.Materials),
    "material_schemas": len(package.Schemas),
    "material_assets": len(package.Assets),
    "edited_density_kg_per_m3": 2870.0,
    "edited_property_count": changed,
    "native_acceptance": "pending for changed bytes",
}
(output / "TypedReemission.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
