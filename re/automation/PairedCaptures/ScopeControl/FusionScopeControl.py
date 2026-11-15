"""Prepare two independent Fusion processes for the P04 scope discovery control."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

REPO = Path(__file__).resolve().parents[4]
BASE = Path("re/automation/PairedCaptures")
STUDY = BASE / "ScopeControl"
SCOPE = "two-body-through-all-discovery"
SCHEMA = 1
PINS = {
    "tool": STUDY / "FusionScopeControl.py",
    "model": STUDY / "FusionScopeModel.py",
    "specification": STUDY / "ScopeControlSpec.json",
    "fresh_process": BASE / "FusionFreshProcess.py",
    "helper": BASE / "FusionCapture.py",
    "bindings": BASE / "FusionBindings.py",
    "control": Path(
        "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
    ),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_input(path, limit=4 * 1024 * 1024):
    require(
        not path.is_symlink() and path.is_file() and 0 < path.stat().st_size <= limit,
        f"Expected a bounded regular input: {path.name}",
    )
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(0 < len(data) <= limit, f"Input changed size: {path.name}")
    return data


def execute_source(relative, data):
    path = REPO / relative
    scope = {"__name__": "__kit_scope_" + path.stem, "__file__": str(path)}
    exec(compile(data, str(path), "exec"), scope)
    return scope


def committed_pin(revision, relative):
    data = subprocess.check_output(
        ["git", "-C", str(REPO), "show", f"{revision}:{relative.as_posix()}"]
    )
    require(
        read_input(REPO / relative) == data, f"Worktree differs from Git: {relative}"
    )
    return {
        "path": relative.as_posix(),
        "size_bytes": len(data),
        "sha256": digest(data),
    }


def read_pin(relative, pin):
    require(pin["path"] == relative.as_posix(), "Prepared input path changed")
    data = read_input(REPO / relative)
    require(
        len(data) == pin["size_bytes"] and digest(data) == pin["sha256"],
        f"Prepared bytes changed: {relative}",
    )
    return data


def prepare(output):
    output = output.resolve()
    require(
        not output.is_relative_to(REPO) and not output.exists(),
        "Choose a new output directory outside the repository",
    )
    revision = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "--verify", "HEAD^{commit}"], text=True
    ).strip()
    pins = {key: committed_pin(revision, path) for key, path in PINS.items()}
    fresh = execute_source(
        PINS["fresh_process"], read_pin(PINS["fresh_process"], pins["fresh_process"])
    )
    model = execute_source(PINS["model"], read_pin(PINS["model"], pins["model"]))
    model["validate_spec"](
        json.loads(read_pin(PINS["specification"], pins["specification"]))
    )
    plan = {"schema": SCHEMA, "scope": SCOPE, "source_revision": revision, "pins": pins}
    output.mkdir()
    plan_path = output / "plan.json"
    plan_hash = fresh["write_json"](plan_path, plan)
    for phase in ("a", "b"):
        fresh["write_new"](
            output / f"phase-{phase}.py",
            fresh["launcher"](
                REPO / PINS["tool"], pins["tool"]["sha256"], plan_path, plan_hash, phase
            ),
        )
    return {
        "run_directory": str(output),
        "source_revision": revision,
        "plan_sha256": plan_hash,
    }


def phases(plan_path, plan_hash):
    data = read_input(plan_path)
    require(digest(data) == plan_hash, "Prepared plan changed")
    plan = json.loads(data)
    require(
        plan["schema"] == SCHEMA
        and plan["scope"] == SCOPE
        and re.fullmatch(r"[0-9a-f]{40}", plan["source_revision"])
        and set(plan["pins"]) == set(PINS),
        "Malformed scope-control plan",
    )
    pins = plan["pins"]
    inputs = {key: read_pin(path, pins[key]) for key, path in PINS.items()}
    spec = json.loads(inputs["specification"])
    model = execute_source(PINS["model"], inputs["model"])
    model["validate_spec"](spec)
    fresh = execute_source(PINS["fresh_process"], inputs["fresh_process"])
    helper = fresh["load_helper"](pins["helper"], pins["bindings"])
    return plan, spec, fresh, helper, model


def prior_report(directory, context, fresh):
    previous_dir = directory / "phase-a"
    require(not previous_dir.is_symlink(), "Phase A output is not a private directory")
    receipt = json.loads(read_input(previous_dir / "receipt.json"))
    data = read_input(previous_dir / "report.json")
    report = json.loads(data)
    require(
        receipt["schema"] == report["schema"] == SCHEMA
        and receipt["scope"] == report["scope"] == SCOPE
        and receipt["phase"] == report["phase"] == "a"
        and receipt["status"] == report["status"] == "complete"
        and receipt["plan_sha256"] == report["plan_sha256"] == context["plan_sha256"]
        and receipt["report_sha256"] == digest(data)
        and report["source_revision"] == context["source_revision"]
        and report["specification_sha256"] == context["specification_sha256"]
        and report["application"] == context["application"]
        and report["application_build"] == context["application_build"]
        and not report["errors"],
        "Phase A receipt is incomplete or outside this exact plan and Fusion build",
    )
    old, current = report["process"], context["process"]
    require(
        old["pid"] != current["pid"]
        and fresh["process_info"](old["pid"]) is None
        and current["start_unix_seconds"] > old["start_unix_seconds"]
        and current["start_unix_seconds"] > report["ended_unix_seconds"],
        "Phase B requires a new Fusion process started after Phase A completed and exited",
    )
    return report, receipt["report_sha256"]


def archive_name(case):
    return f"fusion-{case['mode']}.f3d"


def author_case(app, helper, fresh, model, spec, case, row, output, owned):
    document = model["author"](helper, app, owned, spec, case)
    model["observe"](
        helper,
        fresh,
        document,
        spec,
        case,
        row["before_save"],
        row["before_cut"]["bodies"],
    )
    pin = fresh["save_archive"](helper, document, output, archive_name(case))
    with (output / pin["file"]).open("rb") as stream:
        os.fsync(stream.fileno())
    row["archive"] = pin
    row["authoring_participant_assignment"] = case["input_body_ids"]


def checked_archive(path, pin):
    data = read_input(path, 64 * 1024 * 1024)
    require(
        len(data) == pin["size_bytes"] and digest(data) == pin["sha256"],
        f"Archive bytes differ from Phase A: {path.name}",
    )
    return data


def reopen_case(app, helper, fresh, model, spec, case, row, output, owned):
    pin = row["archive"]
    require(pin["file"] == archive_name(case), "Unexpected sealed Phase A archive name")
    original = output.parent / "phase-a" / pin["file"]
    copy = output / pin["file"]
    fresh["write_new"](copy, checked_archive(original, pin))
    checked_archive(copy, pin)
    reading = row["fresh_import"] = {}
    document = None
    try:
        document = fresh["import_document"](app, copy, reading, owned)
        for label in ("after_reopen", "after_rebuild"):
            if label == "after_rebuild":
                design = helper["design_of"](document)
                require(
                    design.timeline.markerPosition == design.timeline.count,
                    "Cannot recompute with a changed timeline marker",
                )
                reading["compute_all_return"] = design.computeAll()
                require(
                    reading["compute_all_return"] is True,
                    "Fusion refused fresh recompute",
                )
            stage = row[label] = {}
            before_cut = stage["before_cut"] = {"bodies": {}}
            try:
                model["observe"](
                    helper, fresh, document, spec, case, stage, before_cut["bodies"]
                )
            except Exception:
                stage["diagnostic"] = traceback.format_exc()
        require(
            all(
                "diagnostic" not in row[label]
                for label in ("after_reopen", "after_rebuild")
            ),
            "One or more independent observation stages are unresolved",
        )
    finally:
        try:
            if document is not None:
                helper["close"](document, owned)
        finally:
            checked_archive(original, pin)
            checked_archive(copy, pin)
            reading["source_bytes_verified_after_readback"] = True


def close_owned(helper, app, owned):
    for document in list(owned):
        helper["close"](document, owned)
    require(
        app.documents.count == 0,
        "Fusion has a document outside the owned control session",
    )


def execute_cases(app, context, spec, fresh, helper, model, output, prior, owned):
    old_cases = prior["cases"] if prior else ()
    if prior:
        require(
            [row["mode"] for row in old_cases]
            == [case["mode"] for case in spec["cases"]],
            "Phase A case roster disagrees with the pinned specification",
        )
    for index, case in enumerate(spec["cases"]):
        row = (
            {
                "mode": case["mode"],
                "archive": None,
                "before_cut": {"bodies": {}},
                "before_save": {},
                "after_reopen": None,
                "after_rebuild": None,
            }
            if prior is None
            else dict(old_cases[index])
        )
        context["cases"].append(row)
        try:
            if prior is None:
                author_case(app, helper, fresh, model, spec, case, row, output, owned)
            else:
                reopen_case(app, helper, fresh, model, spec, case, row, output, owned)
        except Exception:
            row["diagnostic"] = traceback.format_exc()
            context["errors"].append(case["mode"])
        finally:
            close_owned(helper, app, owned)


def run_phase(plan_path, plan_hash, phase):
    require(
        phase in ("a", "b") and sys.platform == "darwin",
        "Native scope evidence requires a prepared phase on the macOS Fusion host",
    )
    plan, spec, fresh, helper, model = phases(plan_path, plan_hash)
    app = helper["adsk"].core.Application.get()
    require(
        app is not None and app.documents.count == 0,
        "Use an exclusive Fusion session with no open documents",
    )
    process = fresh["process_info"](os.getpid())
    require(process is not None, "Fusion process identity is unavailable")
    report = {
        "schema": SCHEMA,
        "scope": SCOPE,
        "application": "fusion",
        "application_build": app.version,
        "source_revision": plan["source_revision"],
        "specification_sha256": plan["pins"]["specification"]["sha256"],
        "cases": [],
        "errors": [],
        "phase": phase,
        "plan_sha256": plan_hash,
        "process": process,
        "started_unix_seconds": time.time(),
        "pins": plan["pins"],
    }
    prior = None
    if phase == "b":
        prior, previous_hash = prior_report(plan_path.parent, report, fresh)
        report.update(
            previous_phase_report_sha256=previous_hash,
            previous_process=prior["process"],
        )
    output = plan_path.parent / f"phase-{phase}"
    output.mkdir()
    owned = []
    try:
        fresh["measure_control"](
            helper,
            app,
            plan["pins"]["control"],
            owned,
            report,
            "healthy_control_before",
        )
        execute_cases(app, report, spec, fresh, helper, model, output, prior, owned)
        fresh["measure_control"](
            helper, app, plan["pins"]["control"], owned, report, "healthy_control_after"
        )
    except Exception:
        report["errors"].append(traceback.format_exc())
    finally:
        try:
            close_owned(helper, app, owned)
        except Exception:
            report["errors"].append(traceback.format_exc())
        report["ended_unix_seconds"] = time.time()
        report["status"] = "failed" if report["errors"] else "complete"
        report_hash = fresh["write_json"](output / "report.json", report)
        fresh["write_json"](
            output / "receipt.json",
            {
                "schema": SCHEMA,
                "scope": SCOPE,
                "phase": phase,
                "status": report["status"],
                "plan_sha256": plan_hash,
                "report_sha256": report_hash,
            },
        )
    require(
        not report["errors"],
        f"Fusion scope evidence incomplete. Read {output / 'report.json'}",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="new private directory outside the repository",
    )
    print(json.dumps(prepare(parser.parse_args().output), indent=2))
