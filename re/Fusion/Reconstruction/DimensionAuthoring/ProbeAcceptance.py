# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
AUTHORING = Path("re/Fusion/Reconstruction/DimensionAuthoring")
CAPTURES = Path("re/automation/PairedCaptures")
PINS = {
    "acceptance": AUTHORING / "ProbeAcceptance.py",
    "shape": AUTHORING / "ProbeAcceptanceShape.py",
    "fresh_process": CAPTURES / "FusionFreshProcess.py",
    "helper": CAPTURES / "FusionCapture.py",
    "bindings": CAPTURES / "FusionBindings.py",
    "control": Path(
        "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
    ),
}
CANDIDATES = {
    "origin": (
        "OriginCoincidentRectangle.f3d",
        "OriginCoincidenceEvidence.json",
        "ProbeOrigin.py",
    ),
    "owned": ("OwnedRectangle.f3d", "OwnedRectangleEvidence.json", "ProbeOwnedDims.py"),
}
SCHEMA = 1
SCOPE = "fusion-authored-rectangle-candidate"
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def archive_pin(contents):
    return {"sha256": hashlib.sha256(contents).hexdigest(), "size_bytes": len(contents)}


def read_file(path, limit=MAX_METADATA_BYTES):
    require(
        path.is_file() and not path.is_symlink(),
        f"Expected a regular input file: {path}",
    )
    with path.open("rb") as source:
        content = source.read(limit + 1)
    require(0 < len(content) <= limit, f"Input is empty or exceeds its bound: {path}")
    return content


def read_pin(path, pin, limit=MAX_METADATA_BYTES):
    content = read_file(path, limit)
    require(
        all(pin[key] == value for key, value in archive_pin(content).items()),
        f"Prepared bytes changed: {path}",
    )
    return content


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(REPO), *arguments])


def committed_pin(revision, relative):
    expected = git("show", f"{revision}:{relative.as_posix()}")
    require(
        read_file(REPO / relative) == expected, f"Worktree differs from Git: {relative}"
    )
    return archive_pin(expected)


def load_pinned(relative, pin):
    path = REPO / relative
    scope = {"__name__": "__kit_writer_probe_" + path.stem, "__file__": str(path)}
    exec(compile(read_pin(path, pin), str(path), "exec"), scope)
    return scope


def candidate_inputs(directory, kind):
    archive_name, proof_name, probe_name = CANDIDATES[kind]
    proof = read_file(directory / proof_name)
    candidate = read_file(directory / archive_name, MAX_ARCHIVE_BYTES)
    report = json.loads(proof)
    revision = report["codec_revision"]
    require(
        isinstance(revision, str)
        and re.fullmatch("[a-f0-9]{40}", revision)
        and report["native_application_acceptance"] is False,
        "Expected an offline writer proof with a full codec revision",
    )
    probe_pin = archive_pin(
        git("show", f"{revision}:{(AUTHORING / probe_name).as_posix()}")
    )
    require(
        probe_pin["sha256"] == report["probe_sha256"],
        "Probe proof differs from the declared Git revision",
    )
    source_tree = git("rev-parse", "--verify", f"{revision}:src").decode().strip()
    generated = report["generated"]
    if kind == "owned":
        origin = archive_pin(
            git("show", f"{revision}:{(AUTHORING / 'ProbeOrigin.py').as_posix()}")
        )
        require(
            origin["sha256"] == report["origin_probe_sha256"],
            "The owned probe references a different origin generator",
        )
        generated = generated["anchor_evidence"]
    pin = archive_pin(candidate)
    require(
        pin["sha256"] == generated["archive_sha256"]
        and pin["size_bytes"] == generated["archive_bytes"]
        and generated["line_count"] == 4
        and generated["body_count"] == 0,
        "Offline proof does not bind this sketch-only candidate",
    )
    return (
        candidate,
        proof,
        {
            "codec_revision": revision,
            "codec_source_tree": source_tree,
            "input": {"file": archive_name, **pin},
            "proof": {"file": proof_name, **archive_pin(proof)},
        },
    )


def prepare(output, directory, kind):
    output = output.resolve()
    require(
        not output.is_relative_to(REPO) and not output.exists(),
        "Use a new output directory outside the repository",
    )
    revision = git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    pins = {name: committed_pin(revision, path) for name, path in PINS.items()}
    fresh = load_pinned(PINS["fresh_process"], pins["fresh_process"])
    archive, proof, candidate = candidate_inputs(directory, kind)
    plan = {
        "schema": SCHEMA,
        "scope": SCOPE,
        "candidate_kind": kind,
        "prepared_unix_seconds": int(time.time()),
        "source_revision": revision,
        "candidate": candidate,
        "pins": pins,
    }
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    fresh["write_new"](inputs / candidate["input"]["file"], archive)
    fresh["write_new"](inputs / candidate["proof"]["file"], proof)
    plan_path = output / "plan.json"
    plan_hash = fresh["write_json"](plan_path, plan)
    for phase in ("a", "b"):
        tool = REPO / PINS["acceptance"]
        fresh["write_new"](
            output / f"phase-{phase}.py",
            fresh["launcher"](
                tool, pins["acceptance"]["sha256"], plan_path, plan_hash, phase
            ),
        )
    return {"directory": str(output), "plan_sha256": plan_hash, "candidate": candidate}


def prepared_candidate(plan, directory):
    kind = plan["candidate_kind"]
    candidate = plan["candidate"]
    archive_name, proof_name, _ = CANDIDATES[kind]
    require(
        candidate["input"]["file"] == archive_name
        and candidate["proof"]["file"] == proof_name,
        "Prepared candidate names changed",
    )
    inputs = directory / "inputs"
    require(
        inputs.is_dir() and not inputs.is_symlink(), "Prepared input directory changed"
    )
    read_pin(inputs / proof_name, candidate["proof"])
    archive = inputs / archive_name
    read_pin(archive, candidate["input"], MAX_ARCHIVE_BYTES)
    return archive


def observe_sizes(reading, shape, kind, values, orientations):
    for stage in ("before_recompute", "after_recompute"):
        shape["check_rectangle"](reading[stage], kind, values, orientations)


def record_expressions(design):
    return {parameter.name: parameter.expression for parameter in design.allParameters}


def check_support(design):
    root = design.rootComponent
    require(
        root.sketches.item(0).referencePlane == root.xYConstructionPlane,
        "Imported sketch is not bound to the native XY construction plane",
    )


def edit_sizes(document, report, case, fresh, helper, shape, orientations):
    kind = report["candidate_kind"]
    design = helper["design_of"](document)
    initial = report["initial"] = record_expressions(design)
    for axis, (name, value) in enumerate(
        zip(case["parameters"], case["edited_mm"], strict=True)
    ):
        parameter = design.allParameters.itemByName(name)
        require(
            parameter is not None and parameter.expression == initial[name],
            f"Native driver changed before its independent edit: {name}",
        )
        row = report["edits"][name] = {
            "original_expression": initial[name],
            "requested_mm": value,
        }
        expected = list(case["original_mm"])
        expected[axis] = value
        try:
            parameter.expression = f"{value:g} mm"
            outcome = design.computeAll()
            row["edit_compute_all_return"] = outcome
            row["edited"] = fresh["measure"](
                helper, document, f"{name} independently edited"
            )
            require(
                outcome is True,
                f"Fusion did not complete the independent edit rebuild: {name}",
            )
            shape["check_rectangle"](row["edited"], kind, expected, orientations)
            check_support(design)
            expressions = record_expressions(design)
            require(
                {
                    key: expression
                    for key, expression in expressions.items()
                    if key != name
                }
                == {
                    key: expression
                    for key, expression in initial.items()
                    if key != name
                },
                f"An unedited parameter expression changed: {name}",
            )
        finally:
            parameter.expression = initial[name]
            outcome = design.computeAll()
            row["restore_compute_all_return"] = outcome
            row["restored"] = fresh["measure"](helper, document, f"{name} restored")
            require(
                outcome is True and record_expressions(design) == initial,
                f"Fusion did not restore the native parameter expressions: {name}",
            )
            shape["check_rectangle"](
                row["restored"], kind, case["original_mm"], orientations
            )
            check_support(design)


def native_candidate(
    plan, phase, archive, report, first, output, app, fresh, helper, shape, owned
):
    kind = plan["candidate_kind"]
    case = shape["CASES"][kind]
    enum = helper["adsk"].fusion.DimensionOrientations
    orientations = {
        int(enum.HorizontalDimensionOrientation): (0, "right"),
        int(enum.VerticalDimensionOrientation): (1, "upper"),
    }
    if phase == "a":
        source, pin = archive, plan["candidate"]["input"]
    else:
        pin = first["restored_archive"]
        require(pin["file"] == "restored.f3d", "Phase A restored archive name changed")
        source = output.parent / "phase-a" / pin["file"]
        read_pin(source, pin, MAX_ARCHIVE_BYTES)
    reading = report["readback"] = {}
    document = fresh["read_archive"](helper, app, source, pin, owned, reading)
    observe_sizes(reading, shape, kind, case["original_mm"], orientations)
    design = helper["design_of"](document)
    check_support(design)
    if phase == "a":
        report["edits"] = {}
        edit_sizes(document, report, case, fresh, helper, shape, orientations)
        report["restored_archive"] = fresh["save_archive"](
            helper, document, output, "restored.f3d"
        )
    else:
        report["reopened_expressions"] = record_expressions(design)
        require(
            report["reopened_expressions"] == first["initial"],
            "The fresh-process reopen changed the restored native parameter expressions",
        )


def run_phase(plan_path, plan_hash, phase):
    require(
        sys.platform == "darwin",
        "Use the signed-in macOS Fusion oracle for this candidate",
    )
    require(phase in ("a", "b"), "Invalid writer-candidate phase")
    require(plan_path == plan_path.resolve(), "Prepared plan path changed")
    raw = read_file(plan_path)
    require(archive_pin(raw)["sha256"] == plan_hash, "Prepared plan changed")
    plan = json.loads(raw)
    require(
        plan["schema"] == SCHEMA
        and plan["scope"] == SCOPE
        and plan["candidate_kind"] in CANDIDATES
        and set(plan["pins"]) == set(PINS),
        "Invalid writer-candidate plan",
    )
    pins = plan["pins"]
    fresh = load_pinned(PINS["fresh_process"], pins["fresh_process"])
    output = plan_path.parent / f"phase-{phase}"
    output.mkdir(mode=0o700)
    report = {
        "schema": SCHEMA,
        "phase": phase,
        "scope": SCOPE,
        "plan_sha256": plan_hash,
        "candidate_kind": plan["candidate_kind"],
        "source_revision": plan["source_revision"],
        "candidate": plan["candidate"],
        "pins": pins,
        "errors": [],
        "started_unix_seconds": time.time(),
        "claim": "licensed research candidate witness",
    }
    owned = []
    try:
        archive = prepared_candidate(plan, plan_path.parent)
        shape = load_pinned(PINS["shape"], pins["shape"])
        helper = fresh["load_helper"](pins["helper"], pins["bindings"])
        app = helper["adsk"].core.Application.get()
        require(
            app is not None and app.documents.count == 0,
            "Use an exclusive signed-in Fusion process with no open documents",
        )
        process = fresh["process_info"](os.getpid())
        require(
            process is not None
            and process["pid"] == os.getpid()
            and process["start_unix_seconds"] >= plan["prepared_unix_seconds"],
            "Fusion process identity predates the prepared candidate plan",
        )
        report["process"] = process
        report["fusion_version"] = app.version
        first = None
        if phase == "b":
            previous = plan_path.parent / "phase-a"
            require(
                previous.is_dir() and not previous.is_symlink(),
                "Phase A evidence directory changed",
            )
            read_file(previous / "receipt.json")
            read_file(previous / "measurements.json")
            first, first_hash = fresh["prior_capture"](
                plan_path.parent, plan_hash, process
            )
            require(
                first["scope"] == SCOPE
                and first["candidate"] == plan["candidate"]
                and first["fusion_version"] == app.version,
                "Phase B candidate or Fusion build changed",
            )
            report["previous_measurements_sha256"] = first_hash
        fresh["measure_control"](
            helper, app, pins["control"], owned, report, "healthy_control_before"
        )
        try:
            native_candidate(
                plan,
                phase,
                archive,
                report,
                first,
                output,
                app,
                fresh,
                helper,
                shape,
                owned,
            )
        except Exception:
            report["errors"].append(traceback.format_exc())
        finally:
            for document in list(owned):
                try:
                    helper["close"](document, owned)
                except Exception:
                    report["errors"].append(traceback.format_exc())
            fresh["measure_control"](
                helper, app, pins["control"], owned, report, "healthy_control_after"
            )
            require(
                app.documents.count == 0,
                "Fusion retained a document after the owned-document cleanup",
            )
            prepared_candidate(plan, plan_path.parent)
    except Exception:
        report["errors"].append(traceback.format_exc())
        if owned:
            for document in list(owned):
                try:
                    helper["close"](document, owned)
                except Exception:
                    report["errors"].append(traceback.format_exc())
    finally:
        report["ended_unix_seconds"] = time.time()
        report["status"] = "failed" if report["errors"] else "complete"
        measurement_hash = fresh["write_json"](output / "measurements.json", report)
        fresh["write_json"](
            output / "receipt.json",
            {
                "schema": SCHEMA,
                "scope": SCOPE,
                "phase": phase,
                "status": report["status"],
                "measurements_sha256": measurement_hash,
                "plan_sha256": plan_hash,
            },
        )
    require(
        not report["errors"],
        f"Candidate phase failed. See {output / 'measurements.json'}",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Prepare one isolated Fusion writer candidate witness"
    )
    parser.add_argument("--kind", choices=tuple(CANDIDATES), required=True)
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="probe archive and JSON proof directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="new output directory outside the checkout",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.output, args.candidate, args.kind), indent=2))


if __name__ == "__main__":
    main()
