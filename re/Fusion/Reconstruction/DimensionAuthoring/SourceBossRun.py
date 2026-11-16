# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


# Bootstrap with only the sealed plan and its exact shared source before touching Fusion.
def load_contract(plan_path, expected):
    with plan_path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Prepared P03 witness plan changed")
    plan_pin = json.loads(raw)["pins"]["plan"]
    source = Path(__file__).with_name("SourceBossPlan.py").resolve()
    with source.open("rb") as stream:
        code = stream.read(1024 * 1024 + 1)
    if (
        len(code) != plan_pin["size_bytes"]
        or hashlib.sha256(code).hexdigest() != plan_pin["sha256"]
    ):
        raise ValueError("Prepared P03 witness contract changed")
    scope = {"__name__": "__kit_p03_boss_plan__", "__file__": str(source)}
    exec(compile(code, str(source), "exec"), scope)
    return scope


# Match the pinned archive immediately before and after native import and recompute.
def read_archive(context, source, pin, report, owned):
    fresh, helper, measure, contract, app = context
    report["native_input"] = pin
    contract["read_pinned"](source, pin, contract["ARCHIVE_LIMIT"])
    document = fresh["import_document"](app, source, report, owned)
    try:
        label = source.name
        report["before_recompute"] = measure["snapshot"](
            fresh, helper, contract, document, label + " before recompute"
        )
        report["compute_all_return"] = helper["design_of"](document).computeAll()
        report["after_recompute"] = measure["snapshot"](
            fresh, helper, contract, document, label + " after recompute"
        )
        contract["require"](
            report["compute_all_return"] is True, "P03 native import did not rebuild"
        )
    finally:
        contract["read_pinned"](source, pin, contract["ARCHIVE_LIMIT"])
    return document


# Drive one native expression at a time and require a successful restore even on a failed edit.
def edit_dimensions(context, document, report, shape, orientations, original):
    fresh, helper, measure, contract, _ = context
    design = helper["design_of"](document)
    baseline = contract["ORIGINAL_MM"]
    check = measure["check_snapshot"]
    require = contract["require"]
    report["edits"] = {}
    for axis, (name, value) in enumerate(contract["EDITS_MM"].items()):
        parameter = design.allParameters.itemByName(name)
        require(
            parameter is not None and parameter.expression == original[name],
            f"Missing independent P03 driver {name}",
        )
        row = report["edits"][name] = {
            "requested_mm": value,
            "original_expression": original[name],
        }
        sizes = list(baseline)
        sizes[axis] = value
        try:
            parameter.expression = f"{value:g} mm"
            row["edit_compute_all_return"] = design.computeAll()
            row["edited"] = measure["snapshot"](
                fresh, helper, contract, document, f"{name} independently edited"
            )
            expressions = check(row["edited"], sizes, orientations, shape, contract)
            require(
                row["edit_compute_all_return"] is True
                and expressions[name] != original[name]
                and all(
                    expressions[key] == expression
                    for key, expression in original.items()
                    if key != name
                ),
                f"Independent P03 edit changed another driver or failed to rebuild: {name}",
            )
        finally:
            parameter.expression = original[name]
            row["restore_compute_all_return"] = design.computeAll()
            row["restored"] = measure["snapshot"](
                fresh, helper, contract, document, f"{name} restored"
            )
            restored = check(row["restored"], baseline, orientations, shape, contract)
            require(
                row["restore_compute_all_return"] is True and restored == original,
                f"P03 did not restore {name}",
            )


# Run exactly one candidate input between readbacks of the unchanged healthy control.
def capture_candidate(context, source, pin, output, report, shape, prior, owned):
    fresh, helper, measure, contract, _ = context
    enum = helper["adsk"].fusion.DimensionOrientations
    orientations = {
        int(enum.HorizontalDimensionOrientation): (0, "right"),
        int(enum.VerticalDimensionOrientation): (1, "upper"),
    }
    baseline = contract["ORIGINAL_MM"]
    reading = report["readback"] = {}
    document = read_archive(context, source, pin, reading, owned)
    check = measure["check_snapshot"]
    before = check(reading["before_recompute"], baseline, orientations, shape, contract)
    after = check(reading["after_recompute"], baseline, orientations, shape, contract)
    require = contract["require"]
    require(before == after, "P03 recompute changed candidate expressions")
    report["size_orientations"] = {
        str(key): list(value) for key, value in orientations.items()
    }
    if prior is None:
        report["initial"] = after
        edit_dimensions(context, document, report, shape, orientations, after)
        report["restored_archive"] = fresh["save_archive"](
            helper, document, output, "restored.f3d"
        )
    else:
        report["reopened_expressions"] = after
        require(
            after == prior["initial"]
            and report["size_orientations"] == prior["size_orientations"],
            "Fresh P03 reopen did not retain the restored drivers",
        )


# Phase B reads the exact restored archive only after the first process has exited.
def phase_input(contract, fresh, plan, plan_hash, root, process, phase, report):
    source = contract["prepared_input"](root, plan)
    pin = plan["candidate"]["input"]
    prior = None
    if phase == "b":
        contract["direct_directory"](root / "phase-a")
        prior, digest = fresh["prior_capture"](root, plan_hash, process)
        contract["require"](
            prior["errors"] == []
            and all(
                prior[key] == plan[key]
                for key in (
                    "scope",
                    "candidate",
                    "source_revision",
                    "pins",
                    "fusion_version",
                )
            ),
            "Fresh P03 phase does not bind the successful prior process and plan",
        )
        pin = prior["restored_archive"]
        contract["require"](
            pin["file"] == "restored.f3d", "Unexpected P03 restored archive name"
        )
        source = root / "phase-a" / "restored.f3d"
        contract["read_pinned"](source, pin, contract["ARCHIVE_LIMIT"])
        report["previous_measurements_sha256"] = digest
    return source, pin, prior


# Retain diagnostics and failed receipts without certifying an incomplete native run.
def run_phase(plan_path, plan_hash, phase):
    if sys.platform != "darwin" or phase not in ("a", "b"):
        raise ValueError(
            "Use the signed-in macOS Fusion oracle and a prepared P03 phase"
        )
    contract = load_contract(plan_path, plan_hash)
    require = contract["require"]
    require(plan_path == plan_path.resolve(), "Prepared P03 plan path changed")
    plan = contract["read_plan"](plan_path, plan_hash)
    pins = plan["pins"]
    loads, paths = contract["load_helper"], contract["PINS"]
    fresh = loads(paths["fresh_process"], pins["fresh_process"])
    measure = loads(paths["measure"], pins["measure"])
    shape = loads(paths["shape"], pins["shape"])
    output = plan_path.parent / f"phase-{phase}"
    output.mkdir(mode=0o700)
    report = {
        "schema": 1,
        "phase": phase,
        "claim": "licensed P03 research candidate witness",
        "plan_sha256": plan_hash,
        **{key: plan[key] for key in ("scope", "source_revision", "pins", "candidate")},
        "errors": [],
        "started_unix_seconds": time.time(),
    }
    owned = []
    try:
        helper = fresh["load_helper"](pins["helper"], pins["bindings"])
        app = helper["adsk"].core.Application.get()
        require(
            app is not None and app.documents.count == 0,
            "Use an exclusive Fusion process with no open documents",
        )
        report["fusion_version"] = app.version
        require(
            app.version == plan["fusion_version"],
            "Actual Fusion build differs from the prepared P03 plan",
        )
        process = fresh["process_info"](os.getpid())
        require(
            process is not None
            and process["pid"] == os.getpid()
            and process["start_unix_seconds"] >= plan["prepared_unix_seconds"],
            "Fusion process predates the prepared P03 plan",
        )
        report["process"] = process
        source, pin, prior = phase_input(
            contract, fresh, plan, plan_hash, plan_path.parent, process, phase, report
        )
        context = fresh, helper, measure, contract, app
        fresh["measure_control"](
            helper, app, pins["control"], owned, report, "healthy_control_before"
        )
        try:
            capture_candidate(context, source, pin, output, report, shape, prior, owned)
        except Exception:
            report["errors"].append(traceback.format_exc())
        finally:
            close_owned(helper, owned, report)
            fresh["measure_control"](
                helper, app, pins["control"], owned, report, "healthy_control_after"
            )
            require(
                app.documents.count == 0,
                "Fusion retained a document after the P03 cleanup",
            )
            contract["prepared_input"](plan_path.parent, plan)
    except Exception:
        report["errors"].append(traceback.format_exc())
        if owned:
            close_owned(helper, owned, report)
    finally:
        report["ended_unix_seconds"] = time.time()
        report["status"] = "failed" if report["errors"] else "complete"
        digest = fresh["write_json"](output / "measurements.json", report)
        fresh["write_json"](
            output / "receipt.json",
            {
                key: report[key]
                for key in ("schema", "scope", "phase", "status", "plan_sha256")
            }
            | {"measurements_sha256": digest},
        )
    require(
        not report["errors"],
        f"P03 witness phase failed. See {output / 'measurements.json'}",
    )


# Only close documents imported and tracked inside this isolated licensed phase.
def close_owned(helper, owned, report):
    for document in list(owned):
        try:
            helper["close"](document, owned)
        except Exception:
            report["errors"].append(traceback.format_exc())
