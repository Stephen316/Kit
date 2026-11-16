# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from math import isclose
from pathlib import Path
from struct import calcsize
import sys

# Use the established research readers for the source mass and its typed owners.
ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [
    str(ROOT / "re/automation"),
    str(ROOT / "re/solidworks/WriterResearch"),
]

from CmgrBossMass import ReadBossMass
from CmgrColorReadback import ReadColorSpan
from DefinitionTail import ReadPartDefinitionTail
from FusionNeutralRectanglePlan import (
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    VARIANTS,
    map_case,
)
from PairedCaptureIntake import GitSnapshot, require, sha256
from ProbeBossAuthor import generate_boss
from RectanglePairEvidence import capture
from SourceBossProbe import candidate_evidence, source_geometry
from VerifyCmgrBoss import GEOMETRY_TOLERANCES, verify_boss_mass
from VerifyCmgrColor import read_mass_start
from VerifyConfigMat import inspect_material

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

# The established CMgr verification tolerates this absolute deviation in its mass field.
MASS_TOLERANCE_KG = GEOMETRY_TOLERANCES[5]


# The independently framed Definition and Config material records must agree for this solid.
def source_material(archive, generation, layouts):
    definition = archive.require("Contents/Definition")
    definition_start = len(definition) - calcsize("<id")
    density = ReadPartDefinitionTail(definition, definition_start, generation)
    configuration = archive.require("Contents/Config-0")
    start, end, _, _, configured = inspect_material(
        configuration, generation, layouts, density, construct=False
    )
    return {
        "definition_density_kg_m3": density,
        "configuration_density_kg_m3": configured,
        "definition_span": [definition_start, len(definition)],
        "definition_tail_sha256": sha256(definition[definition_start:]),
        "configuration_material_span": [start, end],
        "configuration_material_sha256": sha256(configuration[start:end]),
    }


# Recover the mass cache at the verified typed cursor and reuse its source geometry comparison.
def source_mass(archive, generation, asset, witness):
    stream = archive.require("Contents/CMgr")
    _, _, visual = ReadColorSpan(stream, generation)
    cursor, _ = read_mass_start(stream, visual.Offset)
    start = cursor.Offset
    saved_cursor = FieldCursor(stream, start)
    saved = ReadBossMass(saved_cursor, generation, witness["body_count"])
    wrapper = verify_boss_mass(cursor, archive, generation, witness, asset["path"])
    return {
        "cmgr_mass_span": [start, saved_cursor.Offset],
        "cmgr_mass_options_sha256": wrapper,
        "cmgr_cached_volume_mm3": saved.VolumeM3 * 1e9,
        "cmgr_cached_centroid_mm": [round(value * 1e3, 9) for value in saved.CentroidM],
        "cmgr_cached_mass_kg": saved.MassKg,
        "cmgr_mass_over_volume_kg_m3": saved.MassKg / saved.VolumeM3,
    }


# Confirm that the emitted solid owns the resolved physical asset and has no mass overrides.
def generated_physical(payload, shape):
    model = ReadDocument(payload)
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    material = ReadMaterial(graph, context, model)
    for node in (context.BodyNode, context.Component):
        overrides = ObjectFields(node.Fields["massProperties"])
        require(
            overrides
            == dict.fromkeys(
                ("areaOverride", "densityOverride", "massOverride", "volumeOverride"),
                -1.0,
            ),
            "Generated P03 mass override differs from the uniform body scope",
        )
    volume = shape["cache_volume_mm3"]
    return {
        "solid_owner": shape["solid"],
        "asset_name": material.name,
        "structural_density_kg_m3": material.Density,
        "geometric_volume_mm3": shape["volume_mm3"],
        "geometric_cache_volume_mm3": volume,
        "geometric_cache_centroid_mm": [
            round(value, 9) for value in shape["cache_centroid_mm"]
        ],
        "mass_from_density_and_geometric_cache_kg": material.Density * volume * 1e-9,
        "body_and_component_overrides": "unset",
    }


# Compare the two saved physical representations against the separately reopened source.
def verify_parity(material, mass, target, witness, tolerances):
    require(
        material["definition_density_kg_m3"]
        == material["configuration_density_kg_m3"]
        == target["structural_density_kg_m3"],
        "The Fusion asset density differs from the linked SOLIDWORKS physical records",
    )
    volumes = (
        mass["cmgr_cached_volume_mm3"],
        target["geometric_volume_mm3"],
        target["geometric_cache_volume_mm3"],
    )
    require(
        all(
            isclose(
                value,
                witness["volume_mm3"],
                rel_tol=0,
                abs_tol=tolerances["volume_mm3_absolute"],
            )
            for value in volumes
        )
        and isclose(
            mass["cmgr_cached_mass_kg"],
            target["mass_from_density_and_geometric_cache_kg"],
            rel_tol=0,
            abs_tol=MASS_TOLERANCE_KG,
        ),
        "The authored volume or derived mass disagrees with the pinned source",
    )


# Regenerate only the four measured positive XY P03 geometries and keep native bytes in memory.
def compare_case(snapshot, variant, asset, observed, tolerances, layouts):
    phase, witness = observed
    raw = snapshot.blob(REVISION, asset["path"])
    require(sha256(raw) == asset["sha256"], "P03 source revision differs")
    case = map_case("P03", variant, asset, observed, snapshot, tolerances)
    sizes, edges, body_name, _ = source_geometry(snapshot, case)
    archive = SldprtArchive.from_bytes(raw, asset["path"])
    generation = ContainerMo(archive.streams)
    material = source_material(archive, generation, layouts)
    mass = source_mass(archive, generation, asset, witness)
    payload = generate_boss(variant, sizes, body_name)
    generated = candidate_evidence(case, payload, sizes, edges, witness, tolerances)
    target = generated_physical(payload, generated["target_body"])
    verify_parity(material, mass, target, witness, tolerances)
    return {
        "variant": variant,
        "source_archive_sha256": asset["sha256"],
        "source_reopen_phase": phase,
        "source_licensed_geometry": {
            key: witness[key]
            for key in ("body_count", "volume_mm3", "center_of_mass_mm")
        },
        "source_saved_physical_records": {**material, **mass},
        "generated_fusion_physical_records": target,
    }


# Original archive and measurement pins make the conformance report pool independent.
def report():
    snapshot = GitSnapshot(ROOT)
    raw_spec = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(raw_spec) == SPECIFICATION_SHA256, "P03 specification digest differs"
    )
    specification = snapshot.parse_document(raw_spec, SPECIFICATION)
    (recipe,) = [entry for entry in specification["recipes"] if entry["id"] == "P03"]
    receipt, assets, observations = capture(
        snapshot, recipe, "solidworks", specification
    )
    layouts = LoadPartLayouts()
    tolerances = specification["comparison_tolerances"]
    return {
        "schema": 1,
        "scope": "Offline saved uniform density and derived mass for the positive XY P03 first Boss",
        "source_capture_revision": REVISION,
        "source_specification_sha256": SPECIFICATION_SHA256,
        "source_receipt": receipt["receipt"],
        "source_measurements": receipt["measurements"],
        "target_admission": "unqualified",
        "missing_live_observations": (
            "source assigned material identity and absolute mass",
            "generated Fusion material and absolute mass after edit and fresh-process reopen",
        ),
        "cases": [
            compare_case(
                snapshot,
                variant,
                assets[variant],
                observations[variant],
                tolerances,
                layouts,
            )
            for variant in VARIANTS["P03"]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
