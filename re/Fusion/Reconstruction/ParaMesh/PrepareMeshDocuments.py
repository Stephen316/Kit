import argparse
import hashlib
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    sources = json.loads((ROOT / "re/Fusion/LocalOracle/ParaMesh/Preparation.json").read_text())["cases"]
    source = sources[args.index]
    source_path = ROOT / source["source_file"]
    data = source_path.read_bytes()
    model = ReadDocument(data)
    emitted = EmitParsed(model)
    if ReadDocument(emitted) != model:
        raise ValueError("Complete typed mesh document changed during preparation")
    output = ROOT / "re/Fusion/LocalOracle/MeshDocuments"
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"PreparedMesh{args.index:02}.f3d"
    destination.write_bytes(emitted)
    entry = {
        "name": f"PreparedMesh{args.index:02}", "source_file": source["source_file"],
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "output_file": str(destination.relative_to(ROOT)),
        "output_sha256": hashlib.sha256(emitted).hexdigest(),
        "bytes": len(emitted), "segments": len(model.Segments),
        "records": sum(len(segment.Records) for segment in model.Segments),
        "primary_records": sum(record.IsPrimary for segment in model.Segments for record in segment.Records),
        "mesh_parts": len(model.Meshes), "materials": len(model.Materials),
        "configurations": len(model.Configurations), "snapshots": len(model.Snapshots),
        "body_histories": len(model.Bodies),
        "graphics_objects": len(model.Graphics.Objects) if model.Graphics else 0,
        "mesh_geometry": [{"member": part.Name, "fusion_uuid": part.Mesh.Registry.FusionId,
                           "vertices": len(part.Mesh.Positions), "triangles": len(part.Mesh.Corners) // 3,
                           "face_groups": len(part.Mesh.Registry.Groups)} for part in model.Meshes],
    }
    report_path = output / "Preparation.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {"scope": "Complete production ReadDocument -> EmitParsed: typed segments, meshes, materials, configurations and graphics; preview images retained explicitly", "cases": []}
    report["cases"] = sorted([row for row in report["cases"] if row["name"] != entry["name"]] + [entry], key=lambda row: row["name"])
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main()
