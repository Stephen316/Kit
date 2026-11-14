import argparse
import dataclasses
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from BrepCylinder import Cylinder, build_records
from BrepCylinderBinary import field_token, name_tokens
from BrepTokens import encode_token
from AttributeRecords import attach_attributes
from IdentityModel import DesignIdentity, FeatureTag, HistoryIdentity, SketchLink, StreamProvenance
from JournalRecords import initial_state, insertion_state, preamble


def encode_field(item):
    if item.name == "payload_name":
        return 13, item.value
    if isinstance(item.value, bool):
        return (10 if item.value else 11), None
    return field_token(item)


def serialize_record(record):
    tokens = [*name_tokens(record.name), *(encode_field(item) for item in record.fields), (17, None)]
    return b"".join(encode_token(tag, value) for tag, value in tokens)


def generate(cylinder, design, history, provenance):
    active = attach_attributes(build_records(cylinder), design)
    journal = (preamble(history), insertion_state(history, len(active)), initial_state(history))
    header = b"ASM BinaryFile8" + struct.pack("<4q", 23200, 0, 2, 3)
    header_values = (
        (7, provenance.product), (7, provenance.version), (7, provenance.saved_at),
        (6, provenance.binary_scale_metadata), (6, 1e-6), (6, 1e-10),
    )
    header += b"".join(encode_token(tag, value) for tag, value in header_values)
    end_names = name_tokens("End-of-ASM-History-Section") + name_tokens("End-of-ASM-data")
    ending = b"".join(encode_token(tag, value) for tag, value in end_names)
    data = header + b"".join(serialize_record(record) for record in (*active, *journal)) + ending
    evidence = {
        "artifact_kind": "Independently authored embedded ASM history cylinder; native cache-edit acceptance pending",
        "source_payload_dependencies": [],
        "input_cylinder": dataclasses.asdict(cylinder),
        "input_design_identity": dataclasses.asdict(design),
        "input_history_identity": dataclasses.asdict(history),
        "input_provenance": dataclasses.asdict(provenance),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "header_words": [23200, 0, 2, 3],
        "header_word_roles": ["save format", "unwritten record count", "top-level root count including asmheader", "revision bits and history profile bit"],
        "active_record_count": len(active),
        "history_node_count": 2,
        "insertion_count": len(active) - 1,
        "records": [{"index": index, **dataclasses.asdict(record)} for index, record in enumerate((*active, *journal))],
        "terminal_names": ["End-of-ASM-History-Section", "End-of-ASM-data"],
        "limitations": [
            "Same-source Design body-map and feature identities are supplied explicitly; no surrounding F3D is generated",
            "One insertion-only two-state kernel history profile",
            "Body secondary identity and native history counters are explicit; arbitrary branching and archived revisions remain unsupported",
            "Saved Design body measurements and display meshes are separate caches and may require coherent rewriting",
        ],
    }
    return data, evidence


def load_model(value):
    shape = value["cylinder"]
    cylinder = Cylinder(float(shape["radius_mm"]), float(shape["height_mm"]), tuple(map(float, shape["base_mm"])))
    identity = dict(value["design"])
    for name in ("side_face", "top_face", "bottom_face", "top_edge", "bottom_edge"):
        tag = identity[name]
        identity[name] = FeatureTag(tag["selector"], tag["label"], tuple(tag["operation_ids"]))
    identity["sketch"] = SketchLink(**identity["sketch"])
    identity["authoring_unix_microseconds"] = float(identity["authoring_unix_microseconds"])
    history = dict(value["history"])
    for old, new in (("stream_generation", "stream_current_state_id"), ("allocation_counter", "next_entity_tag"), ("board_number", "board_status")):
        if old in history:
            if new in history:
                raise ValueError("Conflicting legacy history input names")
            history[new] = history.pop(old)
    return cylinder, DesignIdentity(**identity), HistoryIdentity(**history), StreamProvenance(**value["provenance"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    model_bytes = args.model.read_bytes()
    data, evidence = generate(*load_model(json.loads(model_bytes)))
    evidence["semantic_input_sha256"] = hashlib.sha256(model_bytes).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    args.output.with_suffix(".derivation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({name: evidence[name] for name in ("sha256", "bytes", "active_record_count", "insertion_count")}, indent=2))


if __name__ == "__main__":
    main()
