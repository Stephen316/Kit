# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json

from BossInput import ProjectBoss
from FusionBossNativeEvidence import inspect_native
from PairedCaptureIntake import GitSnapshot, recipe_roster, require, sha256
from RectanglePairEvidence import (
    ROOT,
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    capture,
    compare_variant,
    load_public,
)
from convert.Commands.CheckPortable import CheckPortable
from convert.Commands.CheckRetained import KMetadataError
from convert.api import open_document

# Only the baseline and three axis-aligned independent positive edits enter this watch.
VARIANTS = ("baseline-a", "edit-width_mm-41", "edit-height_mm-23", "edit-depth_mm-12")

# An unexpected acceptance or a different first refusal invalidates the diagnostic report.
STRICT_REFUSAL = "Unmodeled native Fusion semantic entity class"

# The public portability check sees the entire retained native archive first.
PORTABLE_REFUSAL = "RetainedPayload records are not conversion-ready; use kit decode or kit research for inspection"


# Capture the actual normal-entry exception from an unchanged native input or neutral projection.
def refusal(action, expected):
    try:
        action()
    except ValueError as error:
        require(str(error) == expected, f"Observed a different first refusal: {error}")
        return str(error)
    raise ValueError(f"Unexpected admission where the evidence expects {expected}")


# Keep the observed neutral contract gaps beside the raw proof and the real entry refusals.
def inspect_gaps(document, raw):
    (retained,) = document.brep_payloads
    (sketch,) = document.sketches
    first, boss = document.feature_timeline
    require(
        retained.id == "fusion-source-archive"
        and retained.format_id == "fusion.f3d"
        and retained.kind == "native_document"
        and retained.data == raw
        and retained.sha256 == sha256(raw)
        and first.kind.value == "native"
        and boss.operation.value == "create"
        and [row.code for row in document.diagnostics]
        == ["fusion.assembly.unsupported", "fusion.history.partial"],
        "Current Fusion partial or retained native state differs from the scoped preflight",
    )
    return {
        "retained_archive": {
            "id": retained.id,
            "kind": retained.kind,
            "sha256": retained.sha256,
            "size_bytes": len(raw),
        },
        "partial_diagnostics": [
            {"code": row.code, "message": row.message} for row in document.diagnostics
        ],
        "source_metadata_keys": sorted(document.metadata),
        "source_sketch_feature": {
            "id": first.id,
            "kind": first.kind.value,
            "entities": len(sketch.entities),
        },
        "source_explicit_coincidences": [
            row.id for row in sketch.constraints if row.kind == "coincident"
        ],
        "source_owned_parameter_count": len(document.parameters),
        "source_taper_parameter": boss.definition.TaperParameterId,
        "unmet_boss_input_contract": (
            "retained native archive",
            "portable reference sketch step",
            "explicit corner joins and fixed origin representation",
            "three independent driving lengths with no neutral expressions",
            "no independently bound taper",
        ),
    }


# The paired report carries authoritative geometry, own-era measurements and actual native operands.
def inspect_pair(snapshot, recipe, variant, sources, observations, tolerances):
    paired = compare_variant(
        snapshot, recipe, variant, sources, observations, None, tolerances
    )
    rectangle, boss = paired["rectangle"], paired["boss"]
    require(
        paired["historical_phases"]
        == {"fusion": "same_process_reopen", "solidworks": "separate_process_reopen"}
        and rectangle["frame"]["origin_mm"] == (0, 0, 0)
        and rectangle["frame"]["axes"] == [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        and rectangle["perimeter"]["status"] == "equal"
        and boss["status"] == "equal"
        and boss["fusion"]["operation"] == "create"
        and boss["solidworks"]["operation"] == "join"
        and boss["fusion"]["displacement_mm"][2] > 0,
        "Paired P03 evidence is outside the original positive XY first-body controls",
    )
    raw, document = load_public(snapshot, sources["fusion"], "fusion")
    native = inspect_native(raw, document, paired, tolerances)
    require(
        native["strict_unmodeled_design_classes"]
        == {"FusionSketchLinearDim": 2, "SketchGeomConstraint": 5},
        "Strict policy observes another native class boundary",
    )
    observed = {
        app: {
            key: row[1][key]
            for key in ("body_count", "volume_mm3", "center_of_mass_mm")
        }
        for app, row in observations.items()
    }
    return {
        "variant": variant,
        "sources": sources,
        "historical_phases": paired["historical_phases"],
        "normal_entry_refusals": {
            "fusion_strict_read": refusal(
                lambda: open_document(raw, source_format="fusion.f3d", strict=True),
                STRICT_REFUSAL,
            ),
            "portable_conversion_guard": refusal(
                lambda: CheckPortable(document), PORTABLE_REFUSAL
            ),
            "solidworks_research_boss_input": refusal(
                lambda: ProjectBoss(document), KMetadataError
            ),
        },
        "neutral_contract_gaps": inspect_gaps(document, raw),
        "native": native,
        "paired_physical_evidence": {
            "selected_lines": rectangle["perimeter"]["matched_links"],
            "maximum_endpoint_delta_mm": rectangle["perimeter"][
                "maximum_endpoint_delta_mm"
            ],
            "positive_world_displacement_mm": boss["fusion"]["displacement_mm"],
            "source_operation": boss["fusion"]["operation"],
            "counterpart_operation": boss["solidworks"]["operation"],
            "observed_bodies": observed,
            "body_comparison": paired["body"],
        },
    }


# Bind both discovery receipts before selecting the four comparison cases.
def report():
    snapshot = GitSnapshot(ROOT)
    raw = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(raw) == SPECIFICATION_SHA256, "Paired recipe specification pin differs"
    )
    spec = snapshot.parse_document(raw, SPECIFICATION)
    recipe = recipe_roster(spec)["P03"]
    applications = ("fusion", "solidworks")
    captures = {app: capture(snapshot, recipe, app, spec) for app in applications}
    first, second = (captures[app][0] for app in applications)
    require(
        first["canonical_recipe_sha256"] == second["canonical_recipe_sha256"]
        and all(set(VARIANTS) <= assets.keys() for _, assets, _ in captures.values()),
        "P03 source and counterpart do not share the exact scoped discovery recipe",
    )
    cases = [
        inspect_pair(
            snapshot,
            recipe,
            variant,
            {app: captures[app][1][variant] for app in applications},
            {app: captures[app][2][variant] for app in applications},
            spec["comparison_tolerances"],
        )
        for variant in VARIANTS
    ]
    return {
        "schema": 1,
        "scope": "unmodified Fusion positive XY P03 first-boss source and SOLIDWORKS input refusals",
        "source_admitted": False,
        "capture_revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "receipts": {
            app: {
                key: capture[key]
                for key in (
                    "receipt",
                    "measurements",
                    "application_build",
                    "qualification_blockers",
                )
            }
            for app, (capture, _, _) in captures.items()
        },
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
