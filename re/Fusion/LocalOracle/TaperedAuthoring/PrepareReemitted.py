import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / "src"))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed


folder = Path(__file__).resolve().parent
preparation = json.loads((folder / "Preparation.json").read_text())
report = {"scope": "Full production typed reading and re-emission of independent tapered documents for native acceptance; no retained Design, history or material payload blocks", "cases": []}
for case in preparation["cases"]:
    source = folder / (case["name"] + ".f3d")
    payload = source.read_bytes()
    model = ReadDocument(payload)
    output = EmitParsed(model)
    target = folder / (case["name"] + "Reemitted.f3d")
    target.write_bytes(output)
    report["cases"].append({
        "name": case["name"],
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "reemitted_sha256": hashlib.sha256(output).hexdigest(),
        "byte_exact": payload == output,
        "bytes": len(output),
        "segments": len(model.Segments),
        "entity_records": sum(len(segment.Records) for segment in model.Segments),
        "body_histories": len(model.Bodies),
        "history_model": type(model.Bodies[0].History).__name__,
        "material_packages": len(model.Materials),
        "material_schemas": sum(len(value.Package.Schemas) for value in model.Materials),
        "material_assets": sum(len(value.Package.Assets) for value in model.Materials),
        "native_acceptance": "identical bytes already accepted" if payload == output else "pending for changed bytes",
    })
(folder / "TypedReemission.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
