"""Compare exact native two-body through-all cut observations offline."""

from argparse import ArgumentParser
from hashlib import file_digest
import json
import math
from pathlib import Path
import re
import sys

from PairedCaptureIntake import GitSnapshot, require, sha256

ROOT = Path(__file__).resolve().parents[2]
SCOPE_FOLDER = "re/automation/PairedCaptures/ScopeControl"
SPEC_PATH = f"{SCOPE_FOLDER}/ScopeControlSpec.json"
SCOPE = "two-body-through-all-discovery"
APPLICATIONS = {"solidworks": ".sldprt", "fusion": ".f3d"}
MODES = ("automatic", "explicit_a", "explicit_ab")
STAGES = ("before_save", "after_reopen", "after_rebuild")
BODY_IDS = ("A", "B")
TOPOLOGY = ("face_count", "edge_count", "vertex_count")


def exact_keys(rows, key, expected, label):
    index = {row[key]: row for row in rows}
    require(len(index) == len(rows) and index.keys() == set(expected), label)
    return index


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def near(first, second, absolute, relative=0.0):
    return (
        finite(first)
        and finite(second)
        and math.isclose(first, second, rel_tol=relative, abs_tol=absolute)
    )


def vector_near(first, second, tolerance):
    return len(first) == len(second) == 3 and all(
        near(a, b, tolerance) for a, b in zip(first, second, strict=True)
    )


def bounds_near(first, second, tolerance):
    return len(first) == len(second) == 2 and all(
        vector_near(a, b, tolerance) for a, b in zip(first, second, strict=True)
    )


def geometry_diff(first, second, tolerances):
    length = tolerances["length_mm_absolute"]
    fields = {
        "bounds_mm": bounds_near(first["bounds_mm"], second["bounds_mm"], length),
        "centroid_mm": vector_near(first["centroid_mm"], second["centroid_mm"], length),
        "volume_mm3": near(
            first["volume_mm3"],
            second["volume_mm3"],
            tolerances["volume_mm3_absolute"],
            tolerances["volume_relative"],
        ),
        **{key: type(first[key]) is int and first[key] == second[key] for key in TOPOLOGY},
    }
    return [key for key, equal in fields.items() if not equal]


def expected_body(bounds, profile=None):
    low, high = bounds
    sizes = [end - start for start, end in zip(low, high, strict=True)]
    centre = [(start + end) / 2 for start, end in zip(low, high, strict=True)]
    volume = math.prod(sizes)
    topology = (6, 12, 8)
    if profile is not None:
        section_low, section_high = profile
        removed = (section_high[0] - section_low[0]) * (section_high[1] - section_low[1]) * sizes[2]
        hole_centre = [(section_low[i] + section_high[i]) / 2 for i in (0, 1)] + [centre[2]]
        centre = [
            (a * volume - b * removed) / (volume - removed)
            for a, b in zip(centre, hole_centre, strict=True)
        ]
        volume -= removed
        topology = (10, 24, 16)
    return {
        "bounds_mm": bounds,
        "centroid_mm": centre,
        "volume_mm3": volume,
        **dict(zip(TOPOLOGY, topology, strict=True)),
    }


def read_spec(snapshot, report):
    revision = report["source_revision"]
    require(re.fullmatch(r"[0-9a-f]{40}", revision), "report source revision is not a full Git SHA")
    raw = snapshot.blob(revision, SPEC_PATH)
    require(sha256(raw) == report["specification_sha256"], "report specification differs from Git")
    value = snapshot.parse_document(raw, "scope specification")
    require(
        value["schema"] == 1
        and value["scope"] == SCOPE
        and value["units"] == "mm"
        and value["bodies"].keys() == set(BODY_IDS),
        "unsupported scope specification",
    )
    operation = value["cut"]
    require(
        operation["end_condition"] == "through_all"
        and operation["depth_mm"] is None
        and operation["direction_world"] == [0, 0, -1]
        and operation["support_body"] == "A",
        "unsupported through-all profile orientation",
    )
    profile_low, profile_high = operation["profile_bounds_mm"]
    body_a = value["bodies"]["A"]["bounds_mm"]
    body_b = value["bodies"]["B"]["bounds_mm"]
    require(
        profile_low[2] == profile_high[2] == body_a[1][2] and body_b[1][2] < body_a[0][2],
        "cut profile and both source solids are not in the witnessed stack",
    )
    for bounds in (body_a, body_b):
        low, high = bounds
        require(
            len(low) == len(high) == 3
            and low[2] < high[2]
            and all(low[i] < profile_low[i] < profile_high[i] < high[i] for i in (0, 1)),
            "through-all profile must be strictly inside both source bodies",
        )
    cases = exact_keys(value["cases"], "mode", MODES, "unsupported scope case roster")
    expected = {
        "automatic": (None, ["A", "B"]),
        "explicit_a": (["A"], ["A"]),
        "explicit_ab": (["A", "B"], ["A", "B"]),
    }
    require(
        all(
            (case["input_body_ids"], case["expected_affected_body_ids"]) == expected[mode]
            for mode, case in cases.items()
        ),
        "unsupported authored scope controls",
    )
    return value, cases


def verify_archive(directory, record, application):
    name = record["file"]
    require(
        re.fullmatch(r"[A-Za-z0-9_.-]+", name)
        and Path(name).suffix.casefold() == APPLICATIONS[application],
        "native archive must be a sibling leaf with the application extension",
    )
    path = directory / name
    require(not path.is_symlink() and path.is_file(), "native archive is not a regular file")
    with path.open("rb") as stream:
        size = stream.seek(0, 2)
        stream.seek(0)
        require(
            type(record["size_bytes"]) is int
            and record["size_bytes"] == size > 0
            and file_digest(stream, "sha256").hexdigest() == record["sha256"],
            "native archive pin mismatch",
        )
    return {key: record[key] for key in ("file", "sha256", "size_bytes")}


def producer(row, expected):
    require(
        row["name"] == expected and type(row["native_id"]) is int and row["native_id"] >= 0,
        "native producer identity differs or is unavailable",
    )
    result = {key: row[key] for key in ("name", "native_id")}
    if "identity_kind" in row:
        require(
            row["identity_kind"] in ("fusion_timeline_index", "solidworks_feature_id"),
            "unsupported native producer identity kind",
        )
        result["identity_kind"] = row["identity_kind"]
    return result


def check_bodies(measured, spec, affected):
    require(measured.keys() == set(BODY_IDS), "exactly two named solid bodies are required")
    values = {}
    for identity, row in measured.items():
        target = spec["bodies"][identity]
        profile = spec["cut"]["profile_bounds_mm"] if identity in affected else None
        comparison = expected_body(target["bounds_mm"], profile)
        differences = geometry_diff(row, comparison, spec["tolerances"])
        require(
            not differences,
            f"body {identity} differs from bounded box witness in {', '.join(differences)}",
        )
        values[identity] = {
            **{key: row[key] for key in comparison},
            "producer": producer(row["producer"], target["producer"]),
        }
    require(
        values["A"]["producer"]["native_id"] != values["B"]["producer"]["native_id"],
        "two bodies resolve to the same native producer",
    )
    return values


def body_ids(ids, label):
    require(
        isinstance(ids, list) and len(ids) == len(set(ids)) and set(ids) <= set(BODY_IDS), label
    )
    return set(ids)


def solidworks_scope(native, policy, target, cut, tolerances):
    enabled, auto = native["feature_scope"], native["auto_select"]
    raw_ids = native["feature_scope_body_ids"]
    require(
        type(enabled) is bool and type(auto) is bool,
        "scope flags must retain native Boolean values",
    )
    resolved = (
        set() if raw_ids is None else body_ids(raw_ids, "unresolved native scope body reference")
    )
    require(
        type(native["feature_scope_body_count"]) is int
        and native["feature_scope_body_count"] == len(resolved),
        "native scope body count does not match its references",
    )
    expected = "automatic" if not enabled or auto else "explicit"
    require(
        policy == expected and (expected == "automatic" or resolved == target),
        "recorded scope policy disagrees with the raw feature-scope fields",
    )
    require(
        native["end_condition"] == 1
        and type(native["reverse_direction"]) is bool
        and native["both_directions"] is False
        and native["support_body_id"] == cut["support_body"]
        and (native["raw_blind_depth_m"] is None or finite(native["raw_blind_depth_m"])),
        "native Cut-Extrude extent, support or depth observation differs",
    )
    keep = (
        "feature_scope",
        "auto_select",
        "feature_scope_body_ids",
        "end_condition",
        "feature_scope_body_count",
        "reverse_direction",
        "both_directions",
        "raw_blind_depth_m",
        "support_body_id",
    )
    result = {key: native[key] for key in keep}
    result["producer"] = producer(native["producer"], cut["feature"])
    result["profile"] = producer(native["profile"], cut["sketch"])
    require(
        result["producer"]["native_id"] != result["profile"]["native_id"],
        "cut and profile resolve to the same native feature",
    )
    if "profile_bounds_mm" in native:
        require(
            bounds_near(
                native["profile_bounds_mm"],
                cut["profile_bounds_mm"],
                tolerances["length_mm_absolute"],
            ),
            "native cut profile bounds differ",
        )
        result["profile_bounds_mm"] = native["profile_bounds_mm"]
    return result


def fusion_scope(native, policy, target, source, tolerance):
    require(policy is None, "Fusion scope intent requires distinct native mode evidence")
    require(
        native["operation"] == 1
        and native["extent_type"] == "adsk::fusion::ThroughAllExtentDefinition"
        and native["start_type"] == "adsk::fusion::ProfilePlaneStartDefinition"
        and native["is_positive_direction"] is False
        and native["has_two_extents"] is False
        and type(native["participant_marker"]) is int
        and native["participant_marker"] >= 0
        and native["participant_count"] == len(target),
        "Fusion native extent or resolved participant count differs",
    )
    support = native["support_cap"]
    require(
        support["status"] == "verified"
        and (
            support["boss_start_face_matches"],
            support["boss_end_face_matches"],
            support["boss_body_matches"],
        )
        == (0, 1, 1)
        and vector_near(support["normal_world"], [0, 0, 1], 1e-9)
        and near(support["signed_offset_mm"], source["profile_bounds_mm"][0][2], tolerance),
        "Fusion Cut does not resolve to the upper end cap of body A",
    )
    return {
        key: native[key]
        for key in (
            "operation",
            "extent_type",
            "start_type",
            "is_positive_direction",
            "has_two_extents",
            "participant_marker",
            "participant_count",
            "support_cap",
        )
    }


def check_stage(stage, before, spec, case, application):
    cut = stage["cut"]
    source = spec["cut"]
    target = body_ids(cut["target_body_ids"], "cut effective bodies are ambiguous")
    require(
        sorted(target) == case["expected_affected_body_ids"]
        and cut["end_condition"] == source["end_condition"]
        and cut["depth_mm"] is None
        and vector_near(cut["direction_world"], source["direction_world"], 1e-9),
        "effective targets or depthless through-all direction differ",
    )
    values = check_bodies(stage["bodies"], spec, target)
    changed = [
        identity
        for identity in BODY_IDS
        if geometry_diff(values[identity], before[identity], spec["tolerances"])
    ]
    require(changed == sorted(target), "effective target bodies differ from measured body changes")
    require(
        all(values[identity]["producer"] == before[identity]["producer"] for identity in BODY_IDS),
        "cut body does not resolve to the same original native producer",
    )
    policy = cut["observed_policy"]
    details = cut["native"]
    if application == "solidworks":
        native = solidworks_scope(details, policy, target, source, spec["tolerances"])
    else:
        require(cut["status"] == "verified", "Fusion Cut archive relationships are unresolved")
        native = fusion_scope(
            details, policy, target, source, spec["tolerances"]["length_mm_absolute"]
        )
    return {
        "cut": {
            **{
                key: cut[key]
                for key in (
                    "depth_mm",
                    "end_condition",
                    "direction_world",
                    "target_body_ids",
                    "observed_policy",
                )
            },
            "native": native,
        },
        "bodies": values,
        "changed_body_ids": changed,
        "requested_policy_observed": (
            None
            if policy is None
            else (policy == ("automatic" if case["input_body_ids"] is None else "explicit"))
        ),
    }


def compare_bodies(first, second, tolerances):
    different = {
        identity: fields
        for identity in BODY_IDS
        if (fields := geometry_diff(first[identity], second[identity], tolerances))
    }
    return {"status": "different" if different else "equal", "different_body_fields": different}


def observe_case(record, spec, case, application, directory):
    archive = verify_archive(directory, record["archive"], application)
    before = check_bodies(record["before_cut"]["bodies"], spec, ())
    stages = {
        stage: check_stage(record[stage], before, spec, case, application) for stage in STAGES
    }
    if application == "fusion":
        require(
            record["authoring_participant_assignment"] == case["input_body_ids"]
            and record["fresh_import"]["source_bytes_verified_after_readback"] is True
            and record["fresh_import"]["compute_all_return"] is True,
            "Fusion authoring assignment, unchanged bytes or fresh rebuild is unproved",
        )
    first = stages["before_save"]
    policy_changes = []
    for stage in STAGES[1:]:
        current = stages[stage]
        require(
            compare_bodies(first["bodies"], current["bodies"], spec["tolerances"])["status"]
            == "equal",
            f"{stage} changes the saved body geometry",
        )
        if application == "solidworks":
            left, right = first["cut"]["native"], current["cut"]["native"]
            require(
                all(
                    left[key] == right[key]
                    for key in (
                        "producer",
                        "profile",
                        "reverse_direction",
                        "support_body_id",
                    )
                ),
                f"{stage} changes the native cut owner, direction or support",
            )
            if any(left[key] != right[key] for key in ("feature_scope", "auto_select")):
                policy_changes.append(stage)
        else:
            repeated_before = check_bodies(record[stage]["before_cut"]["bodies"], spec, ())
            require(
                compare_bodies(before, repeated_before, spec["tolerances"])["status"] == "equal"
                and all(
                    before[identity]["producer"] == repeated_before[identity]["producer"]
                    for identity in BODY_IDS
                ),
                f"{stage} changes the two reopened pre-cut bodies",
            )
            current["before_cut"] = {"bodies": repeated_before}
    return {
        "archive": archive,
        "requested_body_ids": case["input_body_ids"],
        "before_cut": {"bodies": before},
        "native_policy_changes_from_save": policy_changes if application == "solidworks" else None,
        **stages,
    }


def control_comparison(cases, tolerances):
    rows = {}
    for stage in STAGES:
        automatic, one, both = (cases[mode][stage] for mode in MODES)
        nominal = compare_bodies(automatic["bodies"], both["bodies"], tolerances)
        narrowed = compare_bodies(one["bodies"], both["bodies"], tolerances)
        require(
            nominal["status"] == "equal" and narrowed["different_body_fields"].keys() == {"B"},
            f"{stage} controls do not isolate body B while preserving body A",
        )
        first, second = automatic["cut"]["observed_policy"], both["cut"]["observed_policy"]
        rows[stage] = {
            "automatic_vs_explicit_ab": nominal,
            "explicit_a_vs_explicit_ab": narrowed,
            "automatic_vs_explicit_ab_policy": (
                "unobserved"
                if first is None or second is None
                else "equal" if first == second else "different"
            ),
        }
    return rows


def reopen_provenance(report, application):
    if application == "solidworks":
        recorded = report["native_processes"]
        first, second = recorded["authoring"], recorded["reopen"]
        start_field = "started_utc"
        require(
            all(isinstance(row[start_field], str) and row[start_field] for row in (first, second)),
            "SOLIDWORKS process start times are unavailable",
        )
        require(
            first["pid"] != second["pid"]
            and all(row["exited_observed"] is True for row in (first, second)),
            "SOLIDWORKS authoring and reopen process exits are unproved",
        )
        provenance = {"owned_process_exits_observed": True}
    else:
        first, second = report["previous_process"], report["process"]
        require(
            report["phase"] == "b"
            and report["status"] == "complete"
            and not report["errors"]
            and first["pid"] != second["pid"],
            "Fusion did not complete the independent Phase B",
        )
        start_field = "start_unix_seconds"
        require(
            all(finite(row[start_field]) and row[start_field] > 0 for row in (first, second)),
            "Fusion process start times are unavailable",
        )
        provenance = {key: report[key] for key in ("previous_phase_report_sha256", "plan_sha256")}
        require(
            all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in provenance.values()),
            "Fusion report lacks exact previous-phase and plan pins",
        )
    require(
        all(type(row["pid"]) is int and row["pid"] > 0 for row in (first, second))
        and first[start_field] < second[start_field],
        "independent authoring and reopen processes are unproved",
    )
    return {**provenance, "fresh_reopen_observed": True}


def solidworks_sources(snapshot, report):
    revision = report["source_revision"]
    reported = report["sources"]
    paths = {
        "launcher": f"{SCOPE_FOLDER}/RunSolidWorksScope.ps1",
        "collector": f"{SCOPE_FOLDER}/SolidWorksScopeControl.cs",
        "specification": SPEC_PATH,
    }
    require(reported.keys() == paths.keys(), "SOLIDWORKS producer source roster differs")
    for role, path in paths.items():
        data = snapshot.blob(revision, path)
        require(
            reported[role]
            == {
                "path": path,
                "git_blob": snapshot.tree(revision)[path],
                "sha256": sha256(data),
                "size_bytes": len(data),
            },
            f"SOLIDWORKS {role} does not match its Git source",
        )
    return {"source_pins": reported}


def fusion_sources(snapshot, report, directory, digest):
    receipt_path = directory / "receipt.json"
    with receipt_path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, "Fusion scope receipt exceeds its byte limit")
    receipt = snapshot.parse_document(raw, "Fusion scope receipt")
    require(
        receipt
        == {
            "schema": 1,
            "scope": SCOPE,
            "phase": "b",
            "status": "complete",
            "plan_sha256": report["plan_sha256"],
            "report_sha256": digest,
        },
        "Fusion Phase B receipt does not bind the exact report",
    )
    revision = report["source_revision"]
    reported = report["pins"]
    parent = "re/automation/PairedCaptures"
    paths = {
        "tool": f"{SCOPE_FOLDER}/FusionScopeControl.py",
        "model": f"{SCOPE_FOLDER}/FusionScopeModel.py",
        "specification": SPEC_PATH,
        "fresh_process": f"{parent}/FusionFreshProcess.py",
        "helper": f"{parent}/FusionCapture.py",
        "bindings": f"{parent}/FusionBindings.py",
        "control": "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
    }
    require(reported.keys() == paths.keys(), "Fusion producer source roster differs")
    for role, path in paths.items():
        data = snapshot.blob(revision, path)
        require(
            reported[role] == {"path": path, "sha256": sha256(data), "size_bytes": len(data)},
            f"Fusion {role} does not match its Git source",
        )
    return {"source_pins": reported, "receipt_sha256": sha256(raw)}


def read_report(path, expected_digest, application, snapshot):
    require(re.fullmatch(r"[0-9a-f]{64}", expected_digest), "expected a trusted report SHA-256")
    with path.open("rb") as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    require(
        len(raw) <= 4 * 1024 * 1024 and sha256(raw) == expected_digest, "native report pin mismatch"
    )
    report = snapshot.parse_document(raw, "native scope report")
    require(
        report["schema"] == 1
        and report["scope"] == SCOPE
        and report["application"] == application
        and re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", report["application_build"]),
        "native report scope, application or build differs",
    )
    spec, expected = read_spec(snapshot, report)
    provenance = reopen_provenance(report, application)
    if application == "solidworks":
        require(report["application_build"] == "34.4.1.1011", "unsupported SOLIDWORKS scope build")
        provenance.update(solidworks_sources(snapshot, report))
    else:
        provenance.update(fusion_sources(snapshot, report, path.parent, expected_digest))
    records = exact_keys(report["cases"], "mode", MODES, "native scope case roster differs")
    cases = {}
    for mode, record in records.items():
        try:
            cases[mode] = observe_case(record, spec, expected[mode], application, path.parent)
        except (LookupError, TypeError, ValueError) as error:
            raise ValueError(f"{application} {mode}: {error}") from error
    require(
        all(
            len({row["archive"][key] for row in cases.values()}) == len(MODES)
            for key in ("file", "sha256")
        ),
        "scope cases reuse a native archive",
    )
    evidence = {
        **{
            key: report[key]
            for key in ("application_build", "source_revision", "specification_sha256")
        },
        "report_sha256": expected_digest,
        "cases": cases,
        **provenance,
        "controls": control_comparison(cases, spec["tolerances"]),
    }
    return evidence, spec


def compare(inputs):
    snapshot = GitSnapshot(ROOT)
    values = {
        application: read_report(path, digest, application, snapshot)
        for application, (path, digest) in inputs.items()
    }
    reports = {application: evidence for application, (evidence, _) in values.items()}
    result = {"schema": 1, "scope": SCOPE, "qualification": False, "native_reports": reports}
    if reports.keys() == APPLICATIONS.keys():
        solidworks, fusion = (reports[application] for application in APPLICATIONS)
        require(
            solidworks["specification_sha256"] == fusion["specification_sha256"],
            "native reports use different scope specifications",
        )
        tolerances = values["solidworks"][1]["tolerances"]
        result["paired_geometry"] = {
            mode: {
                stage: compare_bodies(
                    solidworks["cases"][mode][stage]["bodies"],
                    fusion["cases"][mode][stage]["bodies"],
                    tolerances,
                )
                for stage in STAGES
            }
            for mode in MODES
        }
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    for application in APPLICATIONS:
        parser.add_argument(f"--{application}", type=Path)
        parser.add_argument(f"--{application}-sha256")
    args = vars(parser.parse_args())
    inputs = {}
    for application in APPLICATIONS:
        path, digest = args[application], args[f"{application}_sha256"]
        if bool(path) != bool(digest):
            parser.error(f"--{application} and --{application}-sha256 must be supplied together")
        if path:
            inputs[application] = (path, digest)
    if not inputs:
        parser.error("supply at least one native evidence report")
    try:
        result = compare(inputs)
        payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    except (LookupError, OSError, TypeError, ValueError) as error:
        parser.exit(1, f"cut scope evidence refused: {error}\n")
    sys.stdout.buffer.write((payload + "\n").encode())


if __name__ == "__main__":
    main()
