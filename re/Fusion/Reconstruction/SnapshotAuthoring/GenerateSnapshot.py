import argparse
import dataclasses
import hashlib
import json
import struct
import sys
from pathlib import Path

research_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(research_root))
sys.path.insert(0, str(research_root / "BrepHistory"))

from BrepCylinder import Cylinder
from BrepCylinderBinary import field_token, name_tokens
from BrepTokens import encode_token
from IdentityModel import FeatureTag, SketchLink, StreamProvenance
from PlanarRegion import CircleRegion
from SnapshotRecords import build_snapshot


def serialize(record):
    fields = [(10 if item.value else 11, None) if isinstance(item.value, bool) else field_token(item) for item in record.fields]
    tokens = [*name_tokens(record.name), *fields, (17, None)]
    return b"".join(encode_token(tag, value) for tag, value in tokens)


def generate(model):
    dimensions = model["cylinder"]
    cylinder = Cylinder(float(dimensions["radius_mm"]), float(dimensions["height_mm"]), tuple(map(float, dimensions["base_mm"])))
    sketch = model["circle"]
    circle = CircleRegion(float(sketch["radius_mm"]), tuple(map(float, sketch["center_mm"])))
    if cylinder.radius_mm != circle.radius_mm or cylinder.base_mm != circle.center_mm:
        raise ValueError("This extrusion snapshot profile requires coincident semantic base circles")
    tags = {name: FeatureTag(value["selector"], value["label"], tuple(value["operation_ids"])) for name, value in model["feature_tags"].items()}
    link = SketchLink(**model["sketch_link"])
    provenance = StreamProvenance(**model["provenance"])
    bindings = model["design_bindings"]
    if len(bindings["passive_scan_ids"]) != 3 or len(set(bindings["passive_scan_ids"])) != 3:
        raise ValueError("Three distinct passive IDs must follow the declared top-level body order")
    records = build_snapshot(cylinder, circle, tags, link)
    header = b"ASM BinaryFile8" + struct.pack("<4q", 23200, 0, 4, 2)
    values = ((7, provenance.product), (7, provenance.version), (7, provenance.saved_at), (6, provenance.binary_scale_metadata), (6, 1e-6), (6, 1e-10))
    header += b"".join(encode_token(tag, value) for tag, value in values)
    data = header + b"".join(serialize(record) for record in records)
    data += b"".join(encode_token(tag, value) for tag, value in name_tokens("End-of-ASM-data"))
    return data, {
        "artifact_kind": "Independently generated three-body snapshot; same-source native acceptance pending",
        "source_payload_dependencies": [],
        "semantic_model": model,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "record_count": len(records),
        "header_words": [23200, 0, 4, 2],
        "header_word_roles": ["save format", "unwritten record count", "top-level roots including asmheader", "revision and no-history profile"],
        "body_roles": [
            {"root_index": 1, "role": "cylinder tool body", "passive_id": bindings["passive_scan_ids"][0]},
            {"root_index": 2, "role": "double-sided sketch region", "passive_id": bindings["passive_scan_ids"][1]},
            {"root_index": 3, "role": "single-sided sketch/profile body", "passive_id": bindings["passive_scan_ids"][2]},
        ],
        "records": [{"index": index, **dataclasses.asdict(record)} for index, record in enumerate(records)],
        "limitations": ["Same-source explicit operation and sketch identities", "Three-root analytic circular extrusion cache profile only", "Design passive-id generator and snapshot serializer remain in the surrounding archive", "This generator does not author a full F3D feature graph"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    semantic_bytes = args.model.read_bytes()
    data, report = generate(json.loads(semantic_bytes))
    report["semantic_input_sha256"] = hashlib.sha256(semantic_bytes).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    args.output.with_suffix(".derivation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({name: report[name] for name in ("sha256", "bytes", "record_count", "body_roles")}, indent=2))


if __name__ == "__main__":
    main()
