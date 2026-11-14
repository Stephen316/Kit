import argparse
import hashlib
import io
import json
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
sys.path.insert(0, str(REPO / "src"))

from convert.formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh
from convert.formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh


def prepare(source_name, output):
    source_path = REPO / source_name
    source = source_path.read_bytes()
    target = io.BytesIO()
    parts = []
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as result:
            for entry in archive.infolist():
                payload = archive.read(entry)
                if entry.filename.endswith(".paramesh"):
                    model = ReadParaMesh(payload)
                    rebuilt = EmitParaMesh(model)
                    if ReadParaMesh(rebuilt) != model:
                        raise ValueError("Prepared mesh semantic model changed")
                    semantic = json.dumps(asdict(model), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                    parts.append({
                        "member": entry.filename,
                        "source_sha256": hashlib.sha256(payload).hexdigest(),
                        "output_sha256": hashlib.sha256(rebuilt).hexdigest(),
                        "semantic_sha256": hashlib.sha256(semantic).hexdigest(),
                        "vertices": len(model.Positions), "triangles": len(model.Corners) // 3,
                        "normal_values": len(model.Normals), "normal_overrides": len(model.Overrides),
                        "feature_edges": len(model.Edges), "face_groups": len(model.Registry.Groups),
                        "fusion_uuid": model.Registry.FusionId,
                        "mesh_uuid": model.Registry.MeshId,
                        "terminal_corner_word": model.TerminalWord,
                    })
                    payload = rebuilt
                result.writestr(entry.filename, payload)
    emitted = target.getvalue()
    output.write_bytes(emitted)
    return {
        "name": output.stem, "source_file": source_name,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "output_file": str(output.relative_to(REPO)),
        "output_sha256": hashlib.sha256(emitted).hexdigest(),
        "bytes": len(emitted), "mesh_parts": parts,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", action="append")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "ContainerFields.json").read_text())["containers"]
    selected = args.archive or list(dict.fromkeys((inventory[0]["archive"], max(inventory, key=lambda row: row["vertices"])["archive"])))
    output = REPO / "re/Fusion/LocalOracle/ParaMesh"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "scope": "Component-native acceptance: only ParaMesh members independently serialized; other source members retained as the native control envelope",
        "cases": [prepare(name, output / f"PreparedMesh{index:02}.f3d") for index, name in enumerate(selected)],
    }
    (output / "Preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"cases": len(report["cases"]), "mesh_parts": sum(len(case["mesh_parts"]) for case in report["cases"]), "report": str(output / "Preparation.json")}))


if __name__ == "__main__":
    main()
