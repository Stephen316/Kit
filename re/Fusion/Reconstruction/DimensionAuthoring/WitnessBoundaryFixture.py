# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import copy
import json
import subprocess
import sys
from pathlib import Path

from ProbeAcceptance import CANDIDATES, archive_pin, git, prepare
from ProbeAcceptanceShape import CASES


def save_record(path, value):
    contents = json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")
    path.write_bytes(contents)
    return archive_pin(contents)["sha256"]


def target(entity):
    return {"status": "resolved", "entity_ids": [entity]}


def snapshot(size):
    width, height = size
    coords = ((0, 0, 0), (width, 0, 0), (width, height, 0), (0, height, 0))
    points = [
        {"id": index, "world_mm": point, "is_origin": index == 0}
        for index, point in enumerate((coords[0], *coords))
    ]
    curves = [
        {
            "id": index,
            "points": {
                "startSketchPoint": target(index + 1),
                "endSketchPoint": target((index + 1) % 4 + 1),
            },
        }
        for index in range(4)
    ]
    constraints = [
        {
            "type": ("HorizontalConstraint", "VerticalConstraint")[index % 2],
            "targets": {"line": target(index)},
        }
        for index in range(4)
    ] + [
        {
            "type": "CoincidentConstraint",
            "targets": {"point": target(1), "entity": target(0)},
        }
    ]
    names = CASES["owned"]["parameters"]
    dimensions = [
        {
            "type": "adsk::fusion::SketchLinearDimension",
            "driving": True,
            "orientation": orientation,
            "parameter": name,
            "targets": {"entityOne": target(1), "entityTwo": target(endpoint)},
        }
        for orientation, name, endpoint in zip((11, 27), names, (2, 4), strict=True)
    ]
    return {
        "design_type": "parametric",
        "body_count": 0,
        "feature_tree": [
            {
                "type": "Sketch",
                "health": {"state": "healthy", "message": None},
                "suppressed": False,
                "rolled_back": False,
            }
        ],
        "sketches": [
            {
                "support": "ConstructionPlane",
                "fully_constrained": True,
                "profile_areas_mm2": [width * height],
                "curves": [
                    {
                        "type": "SketchLine",
                        "construction": False,
                        "fixed": False,
                        "reference": False,
                    }
                ]
                * 4,
                "bindings": {
                    "curves": curves,
                    "points": points,
                    "constraints": constraints,
                    "dimensions": dimensions,
                    "unresolved_constraint_indices": [],
                    "unresolved_dimension_indices": [],
                },
            }
        ],
        "parameters": [
            {
                "name": name,
                "kind": "ModelParameter",
                "expression": f"{value:g} mm",
                "value_internal": value / 10,
            }
            for name, value in zip(names, size, strict=True)
        ],
    }


def generate_plan(directory):
    inputs = directory / "candidate"
    inputs.mkdir()
    archive, proof, tool = CANDIDATES["owned"]
    revision = git("rev-parse", "HEAD").decode().strip()
    authoring = "re/Fusion/Reconstruction/DimensionAuthoring/"
    content = b"synthetic process fixture archive"
    (inputs / archive).write_bytes(content)
    source_pin = archive_pin(git("show", f"{revision}:{authoring}{tool}"))
    origin_pin = archive_pin(git("show", f"{revision}:{authoring}ProbeOrigin.py"))
    save_record(
        inputs / proof,
        {
            "codec_revision": revision,
            "probe_sha256": source_pin["sha256"],
            "origin_probe_sha256": origin_pin["sha256"],
            "native_application_acceptance": False,
            "generated": {
                "anchor_evidence": {
                    "archive_sha256": archive_pin(content)["sha256"],
                    "archive_bytes": len(content),
                    "line_count": 4,
                    "body_count": 0,
                }
            },
        },
    )
    witness = directory / "witness"
    prepared = prepare(witness, inputs, "owned")
    plan = json.loads((witness / "plan.json").read_bytes())
    return witness, prepared["plan_sha256"], plan


def reading(pin, geometry):
    return {
        "native_input": pin,
        "import": {
            "return": "document",
            "exception": None,
            "last_error_on_failure": None,
            "aggregate_loader_warnings": None,
        },
        "compute_all_return": True,
        "before_recompute": copy.deepcopy(geometry),
        "after_recompute": copy.deepcopy(geometry),
    }


def phase(plan, plan_hash, phase_id, start, pin, geometry):
    baseline = {**geometry, "body_count": 1, "volume_mm3": 30000.0}
    control = reading(plan["pins"]["control"], baseline)
    return {
        **{
            key: plan[key]
            for key in (
                "schema",
                "scope",
                "candidate_kind",
                "source_revision",
                "candidate",
                "pins",
            )
        },
        "phase": phase_id,
        "status": "complete",
        "claim": "licensed research candidate witness",
        "plan_sha256": plan_hash,
        "errors": [],
        "process": {
            "pid": 101 if phase_id == "a" else 102,
            "start_unix_seconds": int(start),
        },
        "fusion_version": "2706.1.17",
        "started_unix_seconds": start,
        "ended_unix_seconds": start + 1,
        "healthy_control_before": copy.deepcopy(control),
        "healthy_control_after": copy.deepcopy(control),
        "readback": reading(pin, geometry),
    }


def seal(witness, report):
    directory = witness / f"phase-{report['phase']}"
    report_hash = save_record(directory / "measurements.json", report)
    receipt_hash = save_record(
        directory / "receipt.json",
        {
            **{
                key: report[key]
                for key in ("schema", "scope", "phase", "status", "plan_sha256")
            },
            "measurements_sha256": report_hash,
        },
    )
    return receipt_hash, report_hash


def emit_phases(witness, plan_hash, plan):
    restored_path = witness / "phase-a" / "restored.f3d"
    restored_path.parent.mkdir()
    (witness / "phase-b").mkdir()
    restored_path.write_bytes(b"synthetic restored process fixture archive")
    restored = {"file": restored_path.name, **archive_pin(restored_path.read_bytes())}
    case = CASES["owned"]
    geometry = snapshot(case["original_mm"])
    started = plan["prepared_unix_seconds"] + 1
    initial = {row["name"]: row["expression"] for row in geometry["parameters"]}
    first = phase(plan, plan_hash, "a", started, plan["candidate"]["input"], geometry)
    first["initial"] = initial
    first["restored_archive"] = restored
    first["edits"] = {}
    for axis, name in enumerate(case["parameters"]):
        wanted = case["edited_mm"][axis]
        edited = list(case["original_mm"])
        edited[axis] = wanted
        first["edits"][name] = {
            "original_expression": initial[name],
            "requested_mm": wanted,
            "edit_compute_all_return": True,
            "restore_compute_all_return": True,
            "edited": snapshot(edited),
            "restored": copy.deepcopy(geometry),
        }
    first_pin, measurements_pin = seal(witness, first)
    second = phase(plan, plan_hash, "b", started + 3, restored, geometry)
    second["previous_measurements_sha256"] = measurements_pin
    second["reopened_expressions"] = initial
    return first_pin, second, restored_path


def invoke(witness, plan_pin, first_pin, second_pin, expected=None):
    runner = Path(__file__).with_name("VerifyWitness.py")
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            str(runner),
            "--witness",
            str(witness),
            "--plan-sha256",
            plan_pin,
            "--phase-a-receipt-sha256",
            first_pin,
            "--phase-b-receipt-sha256",
            second_pin,
            "--fusion-version",
            "2706.1.17",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if expected is None:
        assert process.returncode == 0, process.stderr
        return json.loads(process.stdout)
    assert (
        process.returncode == 1 and process.stdout == "" and expected in process.stderr
    ), process
    return None


def exercise(directory):
    witness, plan_pin, plan = generate_plan(directory)
    first_pin, second, restored_path = emit_phases(witness, plan_pin, plan)
    second_pin, _ = seal(witness, second)
    report = invoke(witness, plan_pin, first_pin, second_pin)
    assert report["healthy_control_count"] == 4
    assert report["initial_area_mm2"] == report["reopened_area_mm2"] == 800
    assert report["edited_areas_mm2"] == {"width_mm": 820, "height_mm": 920}
    invoke(witness, plan_pin, first_pin, "0" * 64, "Pinned metadata changed")
    same_process = {**second, "process": {**second["process"], "pid": 101}}
    wrong_pin, _ = seal(witness, same_process)
    invoke(witness, plan_pin, first_pin, wrong_pin, "fresh process")
    wrong_control = copy.deepcopy(second)
    wrong_control["healthy_control_after"]["after_recompute"]["body_count"] = 0
    wrong_pin, _ = seal(witness, wrong_control)
    invoke(witness, plan_pin, first_pin, wrong_pin, "measured solid")
    assert seal(witness, second)[0] == second_pin
    restored_path.write_bytes(b"changed fixture archive")
    invoke(witness, plan_pin, first_pin, second_pin, "Prepared bytes changed")
    return {"verified_synthetic_contract": True, "rejected_mutations": 4}


if __name__ == "__main__":
    print(json.dumps(exercise(Path(sys.argv[1])), sort_keys=True))
