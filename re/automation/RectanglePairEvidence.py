"""Compare the pinned P01 and P03 public rectangle and signed boss evidence."""

from collections import Counter
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from FusionBossDirectionEvidence import (
    RECEIPT as FUSION_BOSS_RECEIPT,
    RECEIPT_SHA256 as FUSION_BOSS_DIGEST,
    SOLIDWORKS_RECEIPT as SW_BOSS_RECEIPT,
    SOLIDWORKS_RECEIPT_SHA256 as SW_BOSS_DIGEST,
)
from FusionBossProfileEvidence import inspect_profile
from FusionCutExtentEvidence import REVISION, SPECIFICATION, SPECIFICATION_SHA256
from FusionCutSketchEvidence import historical_observations
from FusionRectangleSketchEvidence import (
    RECEIPT as FUSION_SKETCH_RECEIPT,
    RECEIPT_SHA256 as FUSION_SKETCH_DIGEST,
    report as fusion_rectangle_report,
)
from PairedCaptureIntake import (
    GitSnapshot,
    inspect_capture,
    recipe_roster,
    require,
    sha256,
)
from PairedPerimeters import edge_gap, match_perimeters
from RectanglePairBoss import compare_boss, fusion_boss, solidworks_boss
from RectanglePairSketch import (
    match_axes,
    match_dimensions,
    match_origin,
    public_scope,
    same,
    xyz,
)

from convert import open_document

RECEIPTS = {
    "P01": {
        "fusion": (FUSION_SKETCH_RECEIPT, FUSION_SKETCH_DIGEST),
        "solidworks": (
            "re/automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json",
            "3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf",
        ),
    },
    "P03": {
        "fusion": (FUSION_BOSS_RECEIPT, FUSION_BOSS_DIGEST),
        "solidworks": (SW_BOSS_RECEIPT, SW_BOSS_DIGEST),
    },
}


def capture(snapshot, recipe, application, specification):
    path, digest = RECEIPTS[recipe["id"]][application]
    parsed = inspect_capture(
        snapshot,
        REVISION,
        path,
        recipe,
        application,
        specification,
        SPECIFICATION_SHA256,
    )
    require(
        parsed["receipt"]["sha256"] == digest and parsed["split"] == "discovery",
        f"{recipe['id']}/{application} capture pin or split differs",
    )
    measurements = snapshot.document(REVISION, parsed["measurements"]["path"])
    if application == "fusion":
        observations = historical_observations(parsed, measurements)
    else:
        require(
            measurements["authoring_process_id"] != measurements["reopen_process_id"],
            "SOLIDWORKS observation did not use an independent reopen",
        )
        instances = measurements["observations"]["reopened_files"]
        observations = {
            asset["variant"]: (
                "separate_process_reopen",
                instances[Path(asset["path"]).name],
            )
            for asset in parsed["native_files"]
        }
    assets = {item["variant"]: item for item in parsed["native_files"]}
    require(
        set(observations) == set(assets), "capture and measured variants do not agree"
    )
    return parsed, assets, observations


def load_public(snapshot, asset, application):
    raw = snapshot.blob(REVISION, asset["path"])
    require(sha256(raw) == asset["sha256"], "public reader input digest differs")
    format_id = "fusion.f3d" if application == "fusion" else "solidworks.sldprt"
    return raw, open_document(
        raw,
        source_format=format_id,
        strict=application == "solidworks",
        include_brep=False,
        include_tessellation=False,
    )


def rectangle_side(document, observed, app, kind, archive, tolerances):
    sketch, frame, entities, perimeter, witness, measured = public_scope(
        document, observed, app, kind, archive, tolerances
    )
    tolerance = tolerances["length_mm_absolute"]
    axes = match_axes(sketch, entities, witness, app, archive)
    dimensions = match_dimensions(
        document,
        sketch,
        frame,
        entities,
        perimeter,
        observed,
        witness,
        app,
        archive,
        tolerance,
    )
    origin = match_origin(sketch, frame, entities, witness, app, archive, tolerance)
    inferred = sum(
        item.kind == "coincident" and item.attributes.get("inferred", False)
        for item in sketch.constraints
    )
    require(
        len(sketch.constraints) == 7 + inferred, "unclassified public rectangle rule"
    )
    return {
        "sketch": sketch,
        "frame": frame,
        "perimeter": perimeter,
        "measured_links": measured["matched_links"],
        "native_support_name": (
            archive["historical_measured_plane"]["plane"]
            if app == "fusion"
            else witness["support_name"]
        ),
        "axes": axes,
        "dimensions": dimensions,
        "origin": origin,
        "inferred_coincidences": inferred,
    }


def status(fusion, solidworks):
    return {
        "status": "equal" if fusion == solidworks else "different",
        "fusion": fusion,
        "solidworks": solidworks,
    }


def paired_dimension(fusion, solidworks, links, tolerance):
    require(
        links[fusion["perimeter_id"]] == solidworks["perimeter_id"]
        and fusion["driving"]
        and solidworks["driving"]
        and abs(fusion["value_mm"] - solidworks["value_mm"]) <= tolerance
        and edge_gap(fusion["operands_world_mm"], solidworks["operands_world_mm"])
        <= tolerance,
        "public dimensions differ on driver role, magnitude or selected side",
    )
    same_order = all(
        math.dist(first, second) <= tolerance
        for first, second in zip(
            fusion["operands_world_mm"], solidworks["operands_world_mm"], strict=True
        )
    )
    return {
        "status": "equal_same_side_and_magnitude",
        "fusion": fusion,
        "solidworks": solidworks,
        "dimension_kind": status(fusion["kind"], solidworks["kind"]),
        "parameter_role": status(
            fusion["parameter_role"], solidworks["parameter_role"]
        ),
        "parameter_unit": status(
            fusion["parameter_unit"], solidworks["parameter_unit"]
        ),
        "ordered_operands": "equal" if same_order else "reversed",
    }


def compare_rectangle(fusion, solidworks, tolerances):
    tolerance = tolerances["length_mm_absolute"]
    correspondence = match_perimeters(
        fusion["perimeter"], solidworks["perimeter"], tolerance
    )
    require(
        correspondence["status"] == "equal",
        f"public perimeter comparison: {correspondence}",
    )
    links = dict(correspondence["matched_links"])
    angle = tolerances["angle_rad_absolute"]
    same(
        xyz(fusion["frame"].origin),
        xyz(solidworks["frame"].origin),
        tolerance,
        "paired public frame origins differ",
    )
    frame_axes = ("x_axis", "y_axis", "z_axis")
    for name in frame_axes:
        same(
            xyz(getattr(fusion["frame"], name)),
            xyz(getattr(solidworks["frame"], name)),
            angle,
            f"paired public {name} differs",
        )
    require(
        {links[key]: kind for key, kind in fusion["axes"].items()}
        == solidworks["axes"],
        "paired axis rules constrain different world sides",
    )
    same(
        fusion["origin"]["world_mm"],
        solidworks["origin"]["world_mm"],
        tolerance,
        "paired origin anchor differs",
    )
    return {
        "perimeter": {
            **correspondence,
            "fusion_world_mm": fusion["perimeter"],
            "solidworks_world_mm": solidworks["perimeter"],
            "fusion_measurement_links": fusion["measured_links"],
            "solidworks_measurement_links": solidworks["measured_links"],
        },
        "frame": {
            "status": "equal",
            "origin_mm": xyz(fusion["frame"].origin),
            "axes": [xyz(getattr(fusion["frame"], name)) for name in frame_axes],
            "native_support_names": status(
                fusion["native_support_name"], solidworks["native_support_name"]
            ),
        },
        "axes": {
            "status": "equal",
            "fusion": fusion["axes"],
            "solidworks": solidworks["axes"],
        },
        "origin": {
            "status": "equal_anchor",
            "fusion": fusion["origin"],
            "solidworks": solidworks["origin"],
        },
        "dimensions": {
            key: paired_dimension(
                value, solidworks["dimensions"][key], links, tolerance
            )
            for key, value in fusion["dimensions"].items()
        },
        "declared_loop": status(
            bool(fusion["sketch"].closed_profile_entity_ids),
            bool(solidworks["sketch"].closed_profile_entity_ids),
        ),
        "inferred_endpoint_coincidences": status(
            fusion["inferred_coincidences"], solidworks["inferred_coincidences"]
        ),
    }


def compare_variant(
    snapshot, recipe, variant, sources, observations, p01_proof, tolerances
):
    fusion_raw, fusion_doc = load_public(snapshot, sources["fusion"], "fusion")
    sw_raw, sw_doc = load_public(snapshot, sources["solidworks"], "solidworks")
    fusion_observed = observations["fusion"][1]
    sw_observed = observations["solidworks"][1]
    has_boss = recipe["id"] == "P03"
    proof = (
        inspect_profile(fusion_raw, variant, recipe, fusion_observed)
        if has_boss
        else None
    )
    fusion_archive = proof["rectangle"] if has_boss else p01_proof
    fusion = rectangle_side(
        fusion_doc, fusion_observed, "fusion", recipe["id"], fusion_archive, tolerances
    )
    sw = rectangle_side(
        sw_doc, sw_observed, "solidworks", recipe["id"], None, tolerances
    )
    rectangle = compare_rectangle(fusion, sw, tolerances)
    result = {
        "recipe_id": recipe["id"],
        "variant": variant,
        "sources": sources,
        "historical_phases": {app: value[0] for app, value in observations.items()},
        "rectangle": rectangle,
    }
    if has_boss:
        result["boss"] = compare_boss(
            fusion_boss(
                fusion_doc, fusion["sketch"], fusion["frame"], proof, tolerances
            ),
            solidworks_boss(sw_doc, sw["sketch"], sw["frame"], sw_raw, tolerances),
            fusion_observed,
            sw_observed,
            proof,
            dict(rectangle["perimeter"]["matched_links"]),
            tolerances,
        )
    return result


def refusal_controls(rows, tolerance):
    baseline = next(
        item
        for item in rows
        if (item["recipe_id"], item["variant"]) == ("P03", "baseline-a")
    )
    reverse = next(
        item
        for item in rows
        if (item["recipe_id"], item["variant"]) == ("P03", "direction-negative")
    )
    rectangle = baseline["rectangle"]["perimeter"]
    fusion, solidworks = rectangle["fusion_world_mm"], rectangle["solidworks_world_mm"]
    duplicate = (*solidworks[:3], ("duplicate-counterpart", solidworks[0][1]))
    ambiguity = match_perimeters(fusion, duplicate, tolerance)
    missing = match_perimeters(fusion, solidworks[1:], tolerance)
    require(
        ambiguity["status"] == "ambiguous"
        and missing["status"] == "different"
        and "matched_links" not in ambiguity
        and "matched_links" not in missing,
        "bad counterpart controls must not publish a perimeter correspondence",
    )
    positive = baseline["boss"]["solidworks"]["displacement_mm"]
    negative = reverse["boss"]["fusion"]["displacement_mm"]
    # Both files have the same world perimeter, so signed extent must distinguish them.
    matched_geometry = match_perimeters(
        solidworks, reverse["rectangle"]["perimeter"]["fusion_world_mm"], tolerance
    )
    require(
        matched_geometry["status"] == "equal"
        and math.dist(positive, negative) > tolerance,
        "signed extent contrast did not distinguish the two saved operations",
    )
    return {
        "duplicate_geometric_counterpart": ambiguity,
        "missing_perimeter_edge": missing,
        "opposite_signed_extent": {
            "status": "different",
            "reason": "opposite measured blind displacements",
            "solidworks_baseline_mm": positive,
            "fusion_reverse_mm": negative,
        },
    }


def report(counterexamples=None):
    first_error = len(counterexamples) if counterexamples is not None else 0
    snapshot = GitSnapshot(ROOT)
    data = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(data) == SPECIFICATION_SHA256, "paired specifications digest differs"
    )
    specification = snapshot.parse_document(data, SPECIFICATION)
    recipes = recipe_roster(specification)
    tolerances = specification["comparison_tolerances"]
    rows, receipts = [], {}
    p01 = fusion_rectangle_report()
    p01_saved = {row["source"]["variant"]: row for row in p01["archives"]}
    for kind in RECEIPTS:
        recipe = recipes[kind]
        left, left_assets, left_observed = capture(
            snapshot, recipe, "fusion", specification
        )
        right, right_assets, right_observed = capture(
            snapshot, recipe, "solidworks", specification
        )
        require(
            left["canonical_recipe_sha256"] == right["canonical_recipe_sha256"]
            and left_assets.keys() == right_assets.keys(),
            "paired discovery recipes or variant rosters differ",
        )
        if kind == "P01":
            require(
                p01["receipt"] == left["receipt"]
                and {variant: row["source"] for variant, row in p01_saved.items()}
                == left_assets,
                "Fusion P01 operand proof uses a different capture",
            )
        receipts[kind] = {
            item["application"]: {
                key: item[key]
                for key in (
                    "receipt",
                    "measurements",
                    "application_build",
                    "qualification_blockers",
                )
            }
            for item in (left, right)
        }
        for variant in sorted(left_assets):
            try:
                rows.append(
                    compare_variant(
                        snapshot,
                        recipe,
                        variant,
                        {
                            "fusion": left_assets[variant],
                            "solidworks": right_assets[variant],
                        },
                        {
                            "fusion": left_observed[variant],
                            "solidworks": right_observed[variant],
                        },
                        p01_saved.get(variant),
                        tolerances,
                    )
                )
            except (KeyError, ValueError) as error:
                if counterexamples is None:
                    raise ValueError(f"{kind}/{variant}: {error}") from error
                counterexamples.append({
                    "recipe": kind,
                    "variant": variant,
                    "sources": {
                        "fusion": left_assets[variant]["sha256"],
                        "solidworks": right_assets[variant]["sha256"],
                    },
                    "reason": str(error)[:2048],
                })
    if counterexamples is not None and len(counterexamples) > first_error:
        return {"pairs": rows}
    require(
        Counter(row["recipe_id"] for row in rows) == {"P01": 6, "P03": 8},
        "unexpected paired discovery roster",
    )
    return {
        "evidence_version": 1,
        "capture_revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "scope": "paired partial-reader discovery evidence for measured rectangles and signed blind bosses",
        "receipts": receipts,
        "pairs": rows,
        "controls": refusal_controls(rows, tolerances["length_mm_absolute"]),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
