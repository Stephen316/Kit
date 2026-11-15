"""Commission an offset-blind numeric search on the pinned Fusion P03 grid."""

import json
from math import isclose
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from FieldSearch import Sample, search
from FusionBossDirectionEvidence import RECEIPT, RECEIPT_SHA256
from FusionCutExtentEvidence import REVISION, SPECIFICATION, SPECIFICATION_SHA256, design_members
from FusionCutSketchEvidence import historical_observations
from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256
from decode_basics import named_features
from fusion_metadata import design_records

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.ParamBinding import ResolveOwner
from convert.formats.Fusion.Sketches.Dimensional.DimRecord import DimRecordBody
from convert.formats.Fusion.Sketches.Dimensional.DimBinding import KDimBindingGuid

CONTROLS = (
    "baseline-a",
    "baseline-b",
    "edit-width_mm-41",
    "edit-height_mm-23",
    "edit-depth_mm-12",
    "units-inch",
    "plane-yz",
    "direction-negative",
)
ROLES = ("parameter", "binding")


def archive_windows(raw):
    streams, members = design_members(raw)
    bulk, meta = streams["BulkStream.dat"], streams["MetaStream.dat"]
    records, _ = design_records(bulk, meta)
    (boss,) = [
        feature
        for feature in named_features(bulk, records)
        if (feature["name"], feature["kind"]) == ("BlindBoss", "Extrude")
    ]
    spans = ReadBulkSpans(bulk, meta)
    owners = {span.ObjectId: span for span in spans if span.IsPrimary}
    require(
        len(owners) == sum(span.IsPrimary for span in spans), "duplicate Fusion primary identity"
    )
    parameters = [
        (span, ReadNativeNum(DimRecordBody(bulk, span)))
        for span in owners.values()
        if span.ClassGuid == KParamGuid
    ]
    ((span, param),) = [
        (span, param)
        for span, param in parameters
        if (param.ParamName, param.RoleName) == ("depth_mm", "AlongDistance")
    ]
    binding = owners.get(param.BindingId)
    require(
        binding is not None and binding.ClassGuid == KDimBindingGuid,
        "P03 parameter has no typed floating-point binding",
    )
    cursor = MetaCursor(DimRecordBody(bulk, binding))
    require(
        cursor.TakeBytes(1) == b"\1"
        and cursor.ReadCount(1) == 1
        and ReadNativeRef(cursor) == boss["object_id"],
        "numeric binding lacks the named Boss owner",
    )
    windows = {}
    for role, selected in zip(ROLES, (span, binding), strict=True):
        body = DimRecordBody(bulk, selected)
        windows[role] = (
            body,
            {
                "class": selected.ClassGuid,
                "object_id": selected.ObjectId,
                "body_offset": selected.PayloadOffset + 4,
                "end_offset": selected.EndOffset,
                "body_sha256": sha256(body),
            },
        )
    return members, boss["object_id"], windows, (bulk, owners, param, span)


def signed_measurement(observation):
    (param,) = [row for row in observation["parameters"] if row["name"] == "depth_mm"]
    require(
        (param["kind"], param["role"]) == ("ModelParameter", "AlongDistance")
        and param["unit"] in ("mm", "in"),
        "historical depth parameter cannot establish a signed length",
    )
    return 10.0 * param["value_internal"], param["unit"]


def locate(windows, scope):
    result = search(windows)
    # Known reader positions corroborate the search only after all candidates have been retained.
    expected = (
        [len(row.body) - 20 for row in windows] if scope == "parameter" else [21] * len(windows)
    )
    for candidate in result["candidates"]:
        candidate["corroborates_existing_reader"] = (
            candidate["encoding"] == "f64:little:cm:signed"
            and [candidate["samples"][row.identity]["body_offset"] for row in windows] == expected
        )
    require(
        sum(row["corroborates_existing_reader"] for row in result["candidates"]) == 1,
        f"bounded search did not corroborate one existing {scope} field",
    )
    return result


def report():
    git = GitSnapshot(ROOT)
    spec_bytes = git.blob(REVISION, SPECIFICATION)
    require(sha256(spec_bytes) == SPECIFICATION_SHA256, "paired specification changed")
    spec = git.parse_document(spec_bytes, SPECIFICATION)
    (recipe,) = [item for item in spec["recipes"] if item["id"] == "P03"]
    baseline = recipe["driving_parameters"]["depth_mm"]
    (edited_depth,) = [
        row["value"] for row in recipe["independent_edits"] if row["parameter"] == "depth_mm"
    ]
    tolerance = spec["comparison_tolerances"]["length_mm_absolute"]
    capture = inspect_capture(git, REVISION, RECEIPT, recipe, "fusion", spec, SPECIFICATION_SHA256)
    require(
        capture["split"] == "discovery" and capture["receipt"]["sha256"] == RECEIPT_SHA256,
        "P03 discovery receipt differs",
    )
    recorded = capture["measurements"]
    measurement_bytes = git.blob(REVISION, recorded["path"])
    require(sha256(measurement_bytes) == recorded["sha256"], "P03 measurement document changed")
    measurements = historical_observations(
        capture, git.parse_document(measurement_bytes, recorded["path"])
    )
    sources = {item["variant"]: item for item in capture["native_files"]}
    require(sources.keys() == set(CONTROLS), "P03 public discovery roster differs")
    samples = {role: [] for role in ROLES}
    provenance = {}
    typed_witnesses = {}
    for variant in CONTROLS:
        source = sources[variant]
        phase, observation = measurements[variant]
        depth, display_unit = signed_measurement(observation)
        expected = {"direction-negative": -baseline, "edit-depth_mm-12": edited_depth}.get(
            variant, baseline
        )
        require(
            isclose(depth, expected, rel_tol=0, abs_tol=tolerance),
            "historical signed depth disagrees with the prescribed experiment value",
        )
        raw = git.blob(REVISION, source["path"])
        require(
            sha256(raw) == source["sha256"] and len(raw) == source["size_bytes"],
            "P03 native archive changed",
        )
        members, boss, windows, typed_witnesses[variant] = archive_windows(raw)
        provenance[variant] = {
            "source": source,
            "observation_phase": phase,
            "measured_signed_depth_mm": depth,
            "search_grid_depth_mm": expected,
            "display_unit": display_unit,
            "boss_object_id": boss,
            "design_members": members,
            "records": {role: row for role, (_, row) in windows.items()},
        }
        for role, (body, _) in windows.items():
            samples[role].append(Sample(variant, expected, body))
    stable = [
        variant for variant in CONTROLS if variant not in ("edit-depth_mm-12", "direction-negative")
    ]
    require(edited_depth > baseline > 0, "independent edits do not distinguish magnitude")
    scans = {role: locate(windows, role) for role, windows in samples.items()}
    for variant, inputs in typed_witnesses.items():
        resolved = ResolveOwner(*inputs)
        require(
            resolved is not None and resolved[0].ObjectId == provenance[variant]["boss_object_id"],
            "saved parameter and binding lack reciprocal owner and value evidence",
        )
    for role, scan in scans.items():
        for candidate in scan["candidates"]:
            for variant, row in candidate["samples"].items():
                row["stream_offset"] = (
                    provenance[variant]["records"][role]["body_offset"] + row["body_offset"]
                )
    return {
        "schema": 1,
        "claim": "known_field_search_commissioning",
        "qualification": False,
        "source_revision": REVISION,
        "application_build": capture["application_build"],
        "recipe": recipe["id"],
        "split": capture["split"],
        "receipt": capture["receipt"],
        "measurements": recorded,
        "specification_sha256": SPECIFICATION_SHA256,
        "observed_signal": "signed blind Boss depth in mm",
        "controls": {
            "same_depth": stable,
            "larger_depth": "edit-depth_mm-12",
            "opposite_direction": "direction-negative",
        },
        "samples": provenance,
        "search": scans,
        "open_claim": "The two stored values covary and their rebuild authority remains unresolved.",
    }


if __name__ == "__main__":
    sys.stdout.buffer.write(
        (json.dumps(report(), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    )
