import io
import json
import sys
import zipfile
from pathlib import Path

from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256


ROOT = Path(__file__).resolve().parents[2]
REVISION = "89c25945f5833ad9c3a1c6c683df510b5702dd54"
SPECIFICATION = "re/automation/PairSpecs.json"
SPECIFICATION_SHA256 = "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
RECEIPT = "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b/receipt.json"
RECEIPT_SHA256 = "8f0c62e6e12cca0b41e91009f929e5d8d823b8977d6344856e6c56a630e05080"
DESIGN = "FusionAssetName[Active]/FusionDesignSegmentType1/"
EXTRUDE_CLASS = "DD405BC2-D673-44F0-8833-5CB2A1C186C7"
MEMBER_LIMIT = 4 * 1024 * 1024

sys.path.insert(0, str(ROOT / "re/Fusion/Study"))
from decode_basics import attach_parameters, named_features
from decode_extrude import decode_extrude
from decode_parameters import decode_stream
from fusion_metadata import design_records


def design_members(content):
    data, evidence = {}, {}
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for leaf in ("BulkStream.dat", "MetaStream.dat"):
            path = DESIGN + leaf
            matching = [member for member in archive.infolist() if member.filename == path]
            require(len(matching) == 1, f"expected one active Design member {path}")
            member = matching[0]
            require(0 < member.file_size <= MEMBER_LIMIT, f"unexpected Design member size: {path}")
            with archive.open(member) as stream:
                body = stream.read(MEMBER_LIMIT + 1)
            require(len(body) == member.file_size, f"Design member size differs from ZIP index: {path}")
            data[leaf] = body
            evidence[leaf] = {"path": path, "size_bytes": len(body), "sha256": sha256(body)}
    return data, evidence


def record_site(data, record):
    return {
        "object_id": record.object_id,
        "class_guid": record.class_guid,
        "class_namespace": record.class_namespace,
        "record_offset": record.start,
        "record_end_offset": record.end,
        "decoded_body_offset": record.body,
        "record_sha256": sha256(data[record.start:record.end]),
        "primary": record.is_primary,
    }


def along_binding(data, parameter):
    offset = parameter["value_offset"]
    return {
        "parameter_name": parameter["parameter_name"],
        "parameter_object_id": parameter["parameter_object_id"],
        "binding_object_id": parameter["binding_object_id"],
        "binding_record_offset": parameter["binding_offset"],
        "value_offset": offset,
        "float64_le_hex": data[offset:offset + 8].hex(),
        "raw_value_cm": parameter["raw_float64"],
        "expression_candidates": parameter["expression_candidates"],
        "recorded_units": parameter["display_units"],
    }


def inspect_archive(content):
    streams, members = design_members(content)
    data = streams["BulkStream.dat"]
    records, framing = design_records(data, streams["MetaStream.dat"])
    by_offset = {record.start: record for record in records}
    features = named_features(data, records)
    parameters, _ = decode_stream(data, records)
    attach_parameters(data, records, features, parameters)
    extrudes = {}
    for feature in features:
        if feature["kind"] != "Extrude":
            continue
        record = by_offset[feature["record_offset"]]
        require(record.is_primary and record.class_guid == EXTRUDE_CLASS, "unexpected extrusion class")
        observation, unresolved = decode_extrude(data[record.body:record.end], feature)
        operation = observation["operation"]["kind"]
        require(operation not in extrudes, f"ambiguous P04 operation: {operation}")
        reference = observation["extrusion_reference_fields"]["target"]
        reference_records = [
            record_site(data, candidate) for candidate in records if candidate.object_id == reference
        ]
        require(reference is None or sum(site["primary"] for site in reference_records) == 1,
                "end reference does not identify one primary object")
        extrudes[operation] = {
            "name": feature["name"],
            "record": record_site(data, record),
            "controls": observation,
            "decoder_unresolved": unresolved,
            "owned_along_distance": [
                along_binding(data, parameter) for parameter in feature["parameters"]
                if parameter["role"] == "AlongDistance"
            ],
            "end_reference_records": reference_records,
            "end_reference_semantics": "unresolved" if reference is not None else None,
        }
    require(set(extrudes) == {"Cut", "NewBody"}, "P04 must have one cut and one NewBody control")
    return {
        "design_members": members,
        "indexed_records": framing["indexed_records"],
        "extrusions": extrudes,
    }


def report():
    git = GitSnapshot(ROOT)
    content = git.blob(REVISION, SPECIFICATION)
    require(sha256(content) == SPECIFICATION_SHA256, "paired specification digest differs")
    specification = git.parse_document(content, SPECIFICATION)
    recipes = [recipe for recipe in specification["recipes"] if recipe["id"] == "P04"]
    require(len(recipes) == 1 and recipes[0]["split"] == "discovery", "unexpected P04 evidence split")
    capture = inspect_capture(git, REVISION, RECEIPT, recipes[0], "fusion", specification, SPECIFICATION_SHA256)
    require(capture["receipt"]["sha256"] == RECEIPT_SHA256, "P04 capture receipt digest differs")
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        "recipe_id": capture["recipe_id"],
        "split": capture["split"],
        "application_build": capture["application_build"],
        "specification_sha256": SPECIFICATION_SHA256,
        "canonical_recipe_sha256": capture["canonical_recipe_sha256"],
        "receipt": capture["receipt"],
        "measurements": capture["measurements"],
        "authoring_provenance": capture["provenance"],
        "capture_qualification_blockers": capture["qualification_blockers"],
        "semantic_qualification": "unverified",
        "native_acceptance": "not_established",
        "archives": [
            {"source": row, **inspect_archive(git.blob(REVISION, row["path"]))}
            for row in capture["native_files"]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
