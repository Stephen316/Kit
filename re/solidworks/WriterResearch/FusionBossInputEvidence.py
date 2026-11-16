# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from io import BytesIO
from math import isclose

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
)
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.api import open_document, write_document
from convert.Commands.CheckPortable import CheckPortable
from convert.Commands.CheckRetained import KMetadataError
from convert.Commands.Qualified.CheckGeometry import KGeometryError
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.Enums.EnumValues import ParameterRole

# Only the baseline and three axis-aligned independent positive edits enter this watch.
VARIANTS = ("baseline-a", "edit-width_mm-41", "edit-height_mm-23", "edit-depth_mm-12")

# Preserve the earlier observed refusal with the source revision that actually produced it.
HISTORICAL = {
    "reader_revision": "dcad571aba31b521cb37e7ccc919cf0bb9667936",
    "report_sha256": "f3a41cd2a17c055d9cae1fd5c879bdfbe614b3dea8fdb14083333f79d04f7ef8",
    "strict_read_refusal": "Unmodeled native Fusion semantic entity class",
}

# The public portability check sees the entire retained native archive first.
PORTABLE_REFUSAL = "RetainedPayload records are not conversion-ready; use kit decode or kit research for inspection"

# The research Boss projection refuses the complete strict graph before remapping its retained topology.
STRICT_BOSS_REFUSAL = (
    "ordinary metric standalone graph with feature history as geometry: "
    "got False, expected True"
)

# The packaged registry reports its own distinct absence of a target write route.
PUBLIC_WRITER_REFUSAL = "no writer registered for solidworks.sldprt"


# Capture the actual normal-entry exception from an unchanged native input or neutral projection.
def refusal(action, expected, error_type=ValueError):
    try:
        action()
    except error_type as error:
        require(str(error) == expected, f"Observed a different first refusal: {error}")
        return str(error)
    raise ValueError(f"Unexpected admission where the evidence expects {expected}")


# Keep the observed neutral contract gaps beside the raw proof and the real entry refusals.
def inspect_partial(document, raw):
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


# Strict admission keeps raw ownership and literal evidence joinable without a portable substitute.
def strict_drivers(document, native):
    drivers = {}
    for parameter in document.parameters:
        source = native[parameter.name]
        unit = "rad" if source["native_unit"] == "deg" else "mm"
        scale = 1 if unit == "rad" else 10
        require(
            parameter.id == f"fusion:0:{source['parameter_object']}"
            and parameter.owner_id == f"fusion:0:{source['owner_feature']}"
            and parameter.role is ParameterRole.KDriving
            and parameter.value.unit == unit
            and isclose(parameter.value.value, scale * source["stored_value"])
            and parameter.expression is not None
            and parameter.expression.source == source["literal"]
            and not parameter.expression.parameter_ids,
            f"Strict driver {parameter.name} differs from its native source binding",
        )
        drivers[parameter.name] = {
            "id": parameter.id,
            "owner": parameter.owner_id,
            "role": parameter.role.value,
            "expression": parameter.expression.source,
            "normalized_value": round(parameter.value.value, 9),
            "normalized_unit": unit,
        }
    require(
        drivers.keys() == native.keys(),
        "Strict driver roster differs from native bindings",
    )
    return drivers


# Keep the complete strict native state including the original physical and presentation records.
def inspect_strict(document, native, raw):
    first, boss = document.feature_timeline
    (sketch,) = document.sketches
    (body,) = document.bodies
    (material,) = document.materials
    drivers = strict_drivers(document, native["direct_parameters"])
    contract = document.metadata["fusion.native_state"]
    restored = CheckContract(contract, "model", 2)
    require(
        first.kind.value == "reference"
        and boss.operation.value == "create"
        and sketch.parameter_ids
        == first.parameter_ids
        == (drivers["width_mm"]["id"], drivers["height_mm"]["id"])
        and boss.parameter_ids == (drivers["depth_mm"]["id"], drivers["d4"]["id"])
        and boss.definition.TaperParameterId == drivers["d4"]["id"]
        and drivers["d4"]["normalized_value"] == 0.0
        and body.material_id == material.id
        and material.name == "PrismMaterial-018"
        and material.Density == 7850.0
        and document.brep is not None
        and document.metadata["fusion.read_only"] is True
        and set(document.metadata) == {"fusion.native_state", "fusion.read_only"}
        and contract["version"] == 2
        and restored == ReadDocument(raw),
        "Strict P03 source lost explicit taper, material, BREP, or complete native state",
    )
    return {
        "status": "admitted",
        "drivers": drivers,
        "sketch_feature": first.id,
        "sketch_profile": sketch.closed_profile_entity_ids,
        "sketch_relations": [relation.id for relation in sketch.constraints],
        "boss_feature": boss.id,
        "taper_parameter": boss.definition.TaperParameterId,
        "body_material": {
            "id": material.id,
            "name": material.name,
            "density_kg_m3": material.Density,
        },
        "preserved_brep": True,
        "typed_native_state": {
            "version": contract["version"],
            "equals_saved_model": True,
            "read_only": True,
        },
    }


# A real public writer request must fail at routing and leave its destination empty.
def public_writer_refusal(document):
    destination = BytesIO()
    message = refusal(
        lambda: write_document(
            document,
            destination,
            destination_format="solidworks.sldprt",
            allow_carrier=False,
        ),
        PUBLIC_WRITER_REFUSAL,
        AdapterNotFoundError,
    )
    require(not destination.getvalue(), "Refused public SOLIDWORKS write emitted bytes")
    return message


# Both normal source routes remain outside public portability and the unchanged research target contract.
def target_refusals(partial, strict):
    return {
        "partial": {
            "portable_conversion_guard": refusal(
                lambda: CheckPortable(partial), PORTABLE_REFUSAL
            ),
            "solidworks_public_write": public_writer_refusal(partial),
            "solidworks_research_boss_input": refusal(
                lambda: ProjectBoss(partial), KMetadataError
            ),
        },
        "strict": {
            "portable_conversion_guard": refusal(
                lambda: CheckPortable(strict), KGeometryError
            ),
            "solidworks_public_write": public_writer_refusal(strict),
            "solidworks_research_boss_input": refusal(
                lambda: ProjectBoss(strict), STRICT_BOSS_REFUSAL, ArchiveError
            ),
        },
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
    raw = snapshot.blob(REVISION, sources["fusion"]["path"])
    require(
        sha256(raw) == sources["fusion"]["sha256"],
        "Fusion source archive digest differs",
    )
    partial = open_document(raw, source_format="fusion.f3d", strict=False)
    strict = open_document(raw, source_format="fusion.f3d", strict=True)
    native = inspect_native(raw, partial, paired, tolerances)
    scoped_classes = native.pop("strict_unmodeled_design_classes")
    require(
        scoped_classes == {"FusionSketchLinearDim": 2, "SketchGeomConstraint": 5},
        "Constrained source differs from the scoped native class roster",
    )
    native["classes_outside_global_allowlist"] = scoped_classes
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
        "strict_source": inspect_strict(strict, native, raw),
        "normal_entry_refusals": target_refusals(partial, strict),
        "partial_source_contract": inspect_partial(partial, raw),
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
        "schema": 2,
        "scope": "unmodified Fusion positive XY P03 first-boss source and SOLIDWORKS input refusals",
        "strict_source_admitted": True,
        "solidworks_target_admitted": False,
        "historical_refusal": HISTORICAL,
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
