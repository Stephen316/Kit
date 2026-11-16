# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass, replace
from math import isclose

from BossInput import LogicalBoss
from BossProfile import ReadLocalProfile
from BossRules import BoundSize, DrivingLength
from FusionBossInputEvidence import target_refusals
from FusionConstrainedPrismEvidence import owned_drivers, sketch_relations
from PairedCaptureIntake import require, sha256
from convert import open_document
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry


# Separate the checked target inputs from the complete source evidence and its losses.
@dataclass(frozen=True, slots=True)
class InverseBoss:
    logical: LogicalBoss
    density_kg_m3: float
    volume_mm3: float
    centroid_mm: tuple[float, float, float]
    evidence: dict[str, object]


# Resolve the selected directed loop through its saved point identities rather than coincident positions.
def source_endpoints(graph, loop):
    by_identity = {node.Identity: node for node in graph.ByClass("Line3D")}
    result = {
        identity: tuple(
            graph.Resolve(by_identity[identity].Fields[field]).Identity
            for field in ("rStartPoint", "rEndPoint")
        )
        for identity in loop
    }
    require(
        len(result) == len(loop) == 4
        and len({pair[0] for pair in result.values()}) == 4
        and all(
            result[before][1] == result[after][0]
            for before, after in zip(loop, (*loop[1:], loop[0]), strict=True)
        ),
        "The exact saved P03 line endpoints do not form one directed closure",
    )
    return result


# Preserve the measured source order while assigning the target's anchor first corner slots.
def source_size(parameter, relation, profile, endpoints, kind, expected_slots):
    refs = tuple(operand.entity_id for operand in relation.references)
    matching = [edge for edge in profile.Edges if endpoints[edge.SourceId] == refs]
    require(
        relation.kind == kind
        and len(matching) == 1
        and set(matching[0].SourceSlots) == set(expected_slots)
        and isclose(
            parameter.value.value,
            abs(
                profile.CornersMm[expected_slots[1]][
                    int(kind is ConstraintKind.KDistanceY)
                ]
            ),
            rel_tol=0.0,
            abs_tol=1e-10,
        ),
        "P03 driver operands do not identify the exact measured source side",
    )
    edge = matching[0]
    bound = BoundSize(
        DrivingLength(
            parameter.id, parameter.name, parameter.owner_id, parameter.value.value
        ),
        relation.id,
        expected_slots,
    )
    return bound, {
        "relation": relation.id,
        "line": edge.SourceId,
        "point_operands": refs,
        "source_corner_slots": edge.SourceSlots,
        "target_corner_slots": expected_slots,
        "value_mm": parameter.value.value,
    }


# Verify the distinct fixed origin before folding its free endpoint identities into target slots.
def source_anchor(sketch, endpoints):
    (anchor,) = [
        relation
        for relation in sketch.constraints
        if relation.kind == ConstraintKind.KCoincident
    ]
    corner, origin = (relation.entity_id for relation in anchor.references)
    (fixed,) = [entity for entity in sketch.entities if entity.fixed]
    require(
        fixed.id == origin
        and fixed.construction
        and isinstance(fixed.geometry, PointGeometry)
        and origin not in {point for pair in endpoints.values() for point in pair}
        and corner in {point for pair in endpoints.values() for point in pair},
        "P03 coincidence does not have the distinct source Origin and shared corner",
    )
    return fixed, {"relation": anchor.id, "ordered_operands": [corner, origin]}


# The strict source continues to retain its complete typed state and reach unchanged public guards.
def source_contract(raw, document, model):
    contract = document.metadata["fusion.native_state"]
    require(
        contract["version"] == 2
        and set(document.metadata) == {"fusion.native_state", "fusion.read_only"}
        and document.metadata["fusion.read_only"] is True
        and CheckContract(contract, "model", 2) == model
        and document.brep is not None
        and model.Bodies
        and model.Snapshots
        and model.Graphics is not None,
        "P03 strict input lost its checked native remainder",
    )
    partial = open_document(raw, source_format="fusion.f3d", strict=False)
    return target_refusals(partial, document)


# Bind the actual source history and mass properties to the independent historical geometry record.
def source_body(document, context, witness):
    (body,) = document.bodies
    (material,) = document.materials
    bounds = body.topology.bounding_box
    low, high = bounds.minimum, bounds.maximum
    cache = ObjectFields(context.BodyNode.Fields["cache"])
    centroid = tuple(value * 10 for value in PointCoords(cache["cog"]))
    volume = body.topology.volume
    require(
        body.material_id == material.id
        and body.final_feature_id == document.feature_timeline[1].id
        and witness["body_count"] == 1
        and (
            body.topology.face_count,
            body.topology.edge_count,
            body.topology.vertex_count,
        )
        == (6, 12, 8)
        and (low.x, low.y, low.z) == (0.0, 0.0, 0.0)
        and all(
            isclose(actual, expected, rel_tol=0, abs_tol=1e-7)
            for actual, expected in zip(
                (high.x, high.y, high.z, volume, *centroid),
                (
                    *witness["bodies"][0]["bounding_box_mm"][1],
                    witness["volume_mm3"],
                    *witness["center_of_mass_mm"],
                ),
                strict=True,
            )
        ),
        "The strict single source cuboid and historical physical observation disagree",
    )
    return body, material, volume, centroid


# Derive only the selected metric positive Boss while retaining a ledger for source only fields.
def read_inverse_source(raw, input_digest, witness, *, configuration):
    require(sha256(raw) == input_digest, "P03 source archive changed")
    document = open_document(raw, source_format="fusion.f3d", strict=True)
    model = ReadDocument(raw)
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    guards = source_contract(raw, document, model)
    drivers = owned_drivers(document, witness)
    topology = sketch_relations(document, graph, context)
    body, material, volume, centroid = source_body(document, context, witness)
    (sketch,) = document.sketches
    (plane,) = document.support_planes
    (loop,) = sketch.closed_profile_entity_ids
    endpoints = source_endpoints(graph, loop)
    fixed, anchor = source_anchor(sketch, endpoints)
    lines = [
        entity
        for entity in sketch.entities
        if isinstance(entity.geometry, LineGeometry)
    ]
    target_outline = replace(sketch, entities=(*lines, fixed))
    profile = ReadLocalProfile(target_outline, plane)
    require(
        profile.AxisCode == 3 and configuration == "Default",
        "Expected fresh Front support and Default configuration",
    )
    width, height, depth, taper = document.parameters
    dimensions = {
        row.parameter_id: row
        for row in sketch.constraints
        if row.parameter_id is not None
    }
    width_bound, width_proof = source_size(
        width,
        dimensions[width.id],
        profile,
        endpoints,
        ConstraintKind.KDistanceX,
        (0, 3),
    )
    height_bound, height_proof = source_size(
        height,
        dimensions[height.id],
        profile,
        endpoints,
        ConstraintKind.KDistanceY,
        (0, 2),
    )
    sketch_step, boss = document.feature_timeline
    require(
        depth.value.value > 0
        and boss.definition.AlongParameterId == depth.id
        and boss.definition.TaperParameterId == taper.id
        and taper.value.value == 0
        and drivers["d4"]["unit"] == "rad"
        and context.Extrude.Identity == boss.id,
        "Expected separately owned positive blind depth and explicit source zero taper",
    )
    logical = LogicalBoss(
        sketch_step.id,
        sketch.name,
        boss.id,
        boss.name,
        body.id,
        body.name,
        configuration,
        profile,
        width_bound,
        height_bound,
        DrivingLength(depth.id, depth.name, depth.owner_id, depth.value.value),
    )
    return InverseBoss(
        logical,
        material.Density,
        volume,
        centroid,
        {
            "archive_sha256": input_digest,
            "neutral_document_sha256": sha256(document.to_json(indent=None).encode()),
            "public_and_research_admission_refusals": guards,
            "selected_loop": topology["perimeter"],
            "shared_endpoint_incidence": endpoints,
            "origin_coincidence": anchor,
            "ordered_dimension_operands": {
                "width_mm": width_proof,
                "height_mm": height_proof,
            },
            "body": {
                "id": body.id,
                "name": body.name,
                "created_by": boss.id,
                "volume_mm3": volume,
                "centroid_mm": centroid,
            },
            "drivers": drivers,
            "source_material": {
                "id": material.id,
                "name": material.name,
                "density_kg_m3": material.Density,
            },
            "untransferred": {
                "editable_taper": {
                    **drivers["d4"],
                    "reason": "The target ordinary Boss has a straight end without an independent taper driver",
                },
                "literal_expression_text": {
                    name: row["expression"]
                    for name, row in drivers.items()
                    if name != "d4"
                },
                "native_material_identity_and_appearance": material.id,
                "source_body_name": body.name,
                "source_configuration_metadata": [
                    {"id": configuration.id, "name": configuration.name}
                    for configuration in document.configurations
                ],
                "native_body_and_cache_parts": {
                    "histories": [part.PartName for part in model.Bodies],
                    "snapshots": [part.Name for part in model.Snapshots],
                    "graphics": model.Graphics is not None,
                },
                "native_only_state": [
                    "Fusion object allocation and persistent identifiers",
                    "Fusion solver and dynamic-update records",
                    "native BREP, surface and history payloads",
                    "Fusion annotation caches and graphical state",
                    "document, configuration and material package metadata",
                ],
            },
        },
    )
