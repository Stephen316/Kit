"""Compare saved P04 neutral history and independent historical observations."""

import argparse
import json
import math
import sys
from pathlib import Path, PurePosixPath

from convert.api.ApiOpen import OpenDocument
from CutHistoryGraph import (
    GraphGap,
    body_metrics,
    effective_axis,
    extent,
    plane_metrics,
    read_history,
    unique,
)
from CutHistorySketch import compare_positioning, measure_profile
from FusionCutExtentEvidence import REVISION
from FusionCutSketchEvidence import historical_observations
from P04FinalBodyEvidence import (
    captures,
    compare,
    compare_captures,
    compare_mass,
    fusion_body,
)
from PairedCaptureIntake import require, sha256
from PairedPerimeters import match_perimeters

APPLICATIONS = {
    "fusion": "fusion.f3d",
    "solidworks": "solidworks.sldprt",
}


def outcome(reader, *values):
    try:
        return reader(*values)
    except GraphGap as error:
        return {"status": error.status, "reason": str(error)}


def classify_body(first, second, tolerances):
    compared = compare(first, second, tolerances)
    equal = compared["counts_exact"] and compared["within_declared_tolerances"]
    return {"status": "equal" if equal else "different", **compared}


def compare_bodies(fusion, solidworks, measured, tolerances):
    public = {
        application: body_metrics(unique(document.bodies, "final body"), application)
        for application, document in (("fusion", fusion), ("solidworks", solidworks))
    }
    comparisons = {
        "between_readers": classify_body(
            public["fusion"], public["solidworks"], tolerances
        ),
        "fusion_to_historical": classify_body(
            public["fusion"], measured["fusion_historical_observation"], tolerances
        ),
    }
    if "solidworks_original_reopen" in measured:
        recorded = measured["solidworks_original_reopen"]
        mass = compare_mass(public["solidworks"], recorded, tolerances)
        equal = recorded["body_count"] == 1 and mass["within_declared_tolerances"]
        comparisons["solidworks_to_original_reopen"] = {
            "status": "equal" if equal else "different",
            "solid_count_exact": recorded["body_count"] == 1,
            **mass,
        }
    else:
        for field, result in (
            ("solidworks_before_rebuild", "solidworks_to_reopen"),
            ("solidworks_after_rebuild", "solidworks_to_rebuild"),
        ):
            comparisons[result] = classify_body(
                public["solidworks"], measured[field], tolerances
            )
    return {
        "status": (
            "equal"
            if all(item["status"] == "equal" for item in comparisons.values())
            else "different"
        ),
        "public": public,
        "comparisons": comparisons,
    }


def compare_extent(fusion, solidworks, cut, tolerance):
    left = extent(fusion.cut if cut else fusion.base, fusion.parameters, cut)
    right = extent(
        solidworks.cut if cut else solidworks.base, solidworks.parameters, cut
    )
    equal = left[0] == right[0] and (
        (left[1] is None and right[1] is None)
        or (
            left[1] is not None
            and right[1] is not None
            and abs(left[1] - right[1]) <= tolerance
        )
    )
    return {
        "status": "equal" if equal else "different",
        "fusion": left,
        "solidworks": right,
    }


def compare_plane(fusion, solidworks, tolerances):
    left, right = plane_metrics(fusion.cut.plane), plane_metrics(solidworks.cut.plane)
    normals = math.dist(left[0], right[0])
    offset = abs(left[1] - right[1])
    equal = (
        normals <= 2 * math.sin(tolerances["angle_rad_absolute"] / 2)
        and offset <= tolerances["length_mm_absolute"]
    )
    return {
        "status": "equal" if equal else "different",
        "fusion_normal_and_offset_mm": left,
        "solidworks_normal_and_offset_mm": right,
        "normal_chord_length": normals,
        "offset_delta_mm": offset,
    }


def compare_axes(fusion, solidworks, role, tolerance):
    left = effective_axis(getattr(fusion, role), fusion.parameters)
    right = effective_axis(getattr(solidworks, role), solidworks.parameters)
    delta = math.dist(left, right)
    return {
        "status": "equal" if delta <= 2 * math.sin(tolerance / 2) else "different",
        "fusion": left,
        "solidworks": right,
        "direction_chord_length": delta,
    }


def summarize_roles(history):
    output = {}
    for key, role in (("base_extrusion", history.base), ("cut", history.cut)):
        output[key] = {
            "operation": str(role.feature.operation),
            "feature": role.feature.id,
            "profile_owner": role.owner.id,
            "profile_sketch": role.sketch.id,
            "input_features": role.feature.input_feature_ids,
        }
    output["support_selection"] = history.support.id
    output["target_selection"] = history.target.id
    output["final_body"] = history.body.id
    return output


def compare_profiles(fusion, solidworks, measured, tolerances):
    tolerance = tolerances["length_mm_absolute"]
    fields = {}
    for role in ("base", "cut"):
        left, right = getattr(fusion, role), getattr(solidworks, role)
        independent_fusion, fusion_match = measure_profile(
            left, measured["fusion"], "fusion", tolerance
        )
        independent_sw, sw_match = measure_profile(
            right, measured["solidworks"], "solidworks", tolerance
        )
        fields[role] = {
            **match_perimeters(left.perimeter, right.perimeter, tolerance),
            "fusion_to_historical": fusion_match,
            "solidworks_to_reopen": sw_match,
        }
        if role == "cut":
            if fields["base"]["status"] == fields["cut"]["status"] == "equal":
                fields["cut_positioning"] = outcome(
                    compare_positioning,
                    fusion,
                    solidworks,
                    independent_fusion,
                    independent_sw,
                    measured["solidworks"],
                    tolerance,
                )
            else:
                fields["cut_positioning"] = {
                    "status": "unclassified",
                    "reason": "requires unique matching base and Cut perimeters",
                }
    return fields


def compare_history(documents, measured, tolerances):
    fusion, solidworks = (read_history(documents[name]) for name in APPLICATIONS)
    length = tolerances["length_mm_absolute"]
    return {
        "status": "bounded_role_correspondence",
        "local_links": {
            "fusion": summarize_roles(fusion),
            "solidworks": summarize_roles(solidworks),
        },
        "profiles": outcome(compare_profiles, fusion, solidworks, measured, tolerances),
        "cut_support_plane": outcome(compare_plane, fusion, solidworks, tolerances),
        "base_extent": outcome(compare_extent, fusion, solidworks, False, length),
        "cut_extent": outcome(compare_extent, fusion, solidworks, True, length),
        "base_direction": outcome(
            compare_axes, fusion, solidworks, "base", tolerances["angle_rad_absolute"]
        ),
        "cut_direction": outcome(
            compare_axes, fusion, solidworks, "cut", tolerances["angle_rad_absolute"]
        ),
        "unclassified": [
            "full sketch constraint, operand and expression correspondence",
            "full authored meaning of the base create versus join operation",
            "SOLIDWORKS persisted through-all body-selection policy",
            "fresh lifecycle-aligned support-face identity and area",
        ],
    }


def read_pair(git, rows, measured):
    documents = {}
    for application, row in rows.items():
        content = git.blob(REVISION, row["path"])
        require(
            sha256(content) == row["sha256"] == measured[f"{application}_sha256"],
            "reader payload differs from the preserved native archive",
        )
        documents[application] = OpenDocument(
            content, SourceFormat=APPLICATIONS[application], StrictMode=False
        )
    return documents


def controls(pairs, historical, tolerances):
    baseline, through_all = (
        pairs[key] for key in ("baseline-a", "termination-through-all")
    )
    left, right = baseline["body"], through_all["body"]
    if "public" not in left or "public" not in right:
        return {
            "status": "unclassified",
            "reason": "body metrics unavailable for termination control",
        }
    results = {
        "public_baseline_solidworks_vs_through_all_fusion": classify_body(
            left["public"]["solidworks"], right["public"]["fusion"], tolerances
        ),
        "baseline_and_through_all_cut_extents": [
            item["history"].get("cut_extent") for item in (baseline, through_all)
        ],
    }
    if historical is not None:
        results["historical_baseline_solidworks_vs_through_all_fusion"] = classify_body(
            historical["baseline-a"]["solidworks_after_rebuild"],
            historical["termination-through-all"]["fusion_historical_observation"],
            tolerances,
        )
    return results


def ambiguous_boundary(document, tolerance):
    edges = read_history(document).cut.perimeter
    duplicate = ("duplicated_geometry_control", edges[0][1])
    return {
        "control": "one baseline Cut boundary candidate copied to a second identity",
        **match_perimeters(edges, (edges[0], duplicate, *edges[2:]), tolerance),
    }


def receipt_document(git, entry):
    path, digest = entry["path"], entry["sha256"]
    contents = git.blob(REVISION, path)
    require(sha256(contents) == digest, "historical measurements digest differs")
    return git.parse_document(contents, path)


def archive_report(context, historical, counterexamples=None):
    first_error = len(counterexamples) if counterexamples is not None else 0
    git, spec, fusion, solidworks = context
    bodies = (
        {row["variant"]: row for row in historical["pairs"]} if historical else None
    )
    tolerances = spec["comparison_tolerances"]
    fusion_api = historical_observations(
        fusion, receipt_document(git, fusion["measurements"])
    )
    sw_api = receipt_document(git, solidworks["measurements"])["observations"][
        "reopened_files"
    ]
    roster = {row["variant"]: {"fusion": row} for row in fusion["native_files"]}
    for row in solidworks["native_files"]:
        roster[row["variant"]]["solidworks"] = row
    pairs = {}
    ambiguous = None
    for variant, rows in roster.items():
        phase, measured_fusion = fusion_api[variant]
        measured_sw = sw_api[PurePosixPath(rows["solidworks"]["path"]).name]
        measured = (
            bodies[variant]
            if bodies is not None
            else {
                **{f"{name}_sha256": row["sha256"] for name, row in rows.items()},
                "fusion_historical_observation": fusion_body(measured_fusion),
                "solidworks_original_reopen": measured_sw,
            }
        )
        try:
            docs = read_pair(git, rows, measured)
        except (KeyError, ValueError) as error:
            if counterexamples is None:
                raise
            counterexamples.append({
                "recipe": "P04",
                "variant": variant,
                "sources": {name: row["sha256"] for name, row in rows.items()},
                "reason": str(error)[:2048],
            })
            continue
        if historical is None and variant == "baseline-a":
            ambiguous = outcome(
                ambiguous_boundary, docs["fusion"], tolerances["length_mm_absolute"]
            )
        pairs[variant] = {
            "sources": {
                name: {"path": row["path"], "sha256": row["sha256"]}
                for name, row in rows.items()
            },
            "fusion_historical_phase": phase,
            "body": outcome(
                compare_bodies,
                docs["fusion"],
                docs["solidworks"],
                measured,
                tolerances,
            ),
            "history": outcome(
                compare_history,
                docs,
                {"fusion": measured_fusion, "solidworks": measured_sw},
                tolerances,
            ),
        }
    if counterexamples is not None and len(counterexamples) > first_error:
        return {"pairs": pairs, "historical_body_evidence": historical}
    result = {
        "scope": "P04 discovery archives and independent historical measurements",
        "capture_receipts": {
            name: value["receipt"]
            for name, value in (("fusion", fusion), ("solidworks", solidworks))
        },
        "original_measurements": {
            name: value["measurements"]
            for name, value in (("fusion", fusion), ("solidworks", solidworks))
        },
        "pairs": pairs,
        "termination_difference_control": controls(pairs, bodies, tolerances),
        "fresh_native_fusion": "unverified",
        "generic_comparator_qualification": "unverified",
    }
    if historical is not None:
        result["historical_body_evidence"] = historical
    else:
        result["declared_tolerances"] = tolerances
        result["capture_revision"] = REVISION
        result["ambiguous_boundary_control"] = ambiguous
        result["body_evidence_scope"] = {
            "fusion_historical": "saved counts, bounds, volume and center",
            "solidworks_original_reopen": "solid count, volume and center",
            "solidworks_supplemental_readback": "separate receipt required",
        }
    return result


def report(directory, receipt_digest, counterexamples=None):
    context = captures()
    return archive_report(
        context,
        compare_captures(context, directory, receipt_digest),
        counterexamples,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readback_directory", type=Path, nargs="?")
    parser.add_argument("--receipt-sha256")
    parser.add_argument("--git-only", action="store_true")
    options = parser.parse_args()
    if options.git_only:
        if options.readback_directory is not None or options.receipt_sha256 is not None:
            parser.error(
                "--git-only uses the original Git receipts without a readback directory"
            )
        result = archive_report(captures(), None)
    else:
        if options.readback_directory is None or options.receipt_sha256 is None:
            parser.error(
                "a licensed readback directory and --receipt-sha256 are required outside --git-only"
            )
        result = report(options.readback_directory, options.receipt_sha256)
    sys.stdout.buffer.write(
        (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    )
