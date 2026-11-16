# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from collections import Counter
from dataclasses import replace
from io import BytesIO
from math import isclose
from pathlib import Path
import sys
from zipfile import ZipFile

# The research decoder uses the existing discovery receipts and captures.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/automation"))

from FusionConstrainedPrismEvidence import POSITIVE, REFUSED, refusal
from FusionCutExtentEvidence import REVISION, SPECIFICATION, SPECIFICATION_SHA256
from PairedCaptureIntake import GitSnapshot, require, sha256
from ReadSignedPrism import face_areas, read_signed_prism
from RectanglePairEvidence import capture
from convert import open_document
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Parameters.ReadParameters import CheckBinding
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion
from convert.adapters.Fusion.Native.Policy.CheckPlacement import CheckMatrix
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.CheckSideRecipe import CheckSideRecipe
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadLine import ReadLine
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

# These independently measured discovery archives exclude all unrelated profiles.
CASES = {
    **{name: value for name, value in POSITIVE.items() if name != "baseline-b"},
    "direction-negative": REFUSED["direction-negative"][0],
}


# Read just the two exact parts designated by the typed document manifest.
def body_parts(raw, model):
    (body,) = model.Bodies
    (snapshot,) = model.Snapshots
    with ZipFile(BytesIO(raw)) as archive:
        result = []
        for relative in (body.PartName, snapshot.Name):
            (name,) = [
                name for name in archive.namelist() if name.endswith("/" + relative)
            ]
            result.append(archive.read(name))
        return tuple(result)


# The native selected loop supplies each physical curve and its separately checked side recipe.
def design_curves(graph, context, asset_id):
    nodes = OrderLines(graph, graph.ByClass("Line3D"))
    lines = tuple(ReadLine(graph, node, (0.0, 0.0, 1.0)) for node in nodes)
    CheckRegion(graph, context, nodes, asset_id)
    curves = {
        CurveTag(node): frozenset(
            ((line.start.x / 10, line.start.y / 10), (line.end.x / 10, line.end.y / 10))
        )
        for node, line in zip(nodes, lines, strict=True)
    }
    require(len(curves) == 4, "Expected four uniquely tagged selected profile sides")
    points = {point for endpoints in curves.values() for point in endpoints}
    shape = RectGeometry(
        (),
        lines,
        nodes,
        10 * max(point[0] for point in points),
        10 * max(point[1] for point in points),
        (0.0, 0.0, 0.0),
    )
    table = ResolveField(graph, context.Extrude, "rProgenitorTable", "ProgenitorTable")
    sides, body = {}, []
    for pair in SeriesItems(table.Fields["ProgenitorTagVec"]):
        owner = graph.Resolve(pair.First)
        if owner.ClassName == "BodyProgenitor":
            body.append((owner, pair.Second))
        else:
            require(
                owner.ClassName == "SketchCurveProgenitor",
                "Unexpected side progenitor class",
            )
            recipe = ResolveField(graph, owner, "rRecipe", "SketchCurveRecipe")
            tag = CheckSideRecipe(recipe.Fields["profileEdgeTagData"], shape)
            sides[str(pair.Second)] = tag
    require(
        set(sides) == {"3", "4", "5", "6"} and set(sides.values()) == set(curves),
        "Side progenitors do not cover the native profile",
    )
    (progenitor,) = body
    return curves, sides, progenitor


# Collect typed live attributes with their actual native owner slots and reject duplicates.
def face_and_body_tags(table):
    result = {}
    for slot in table.LiveSlots:
        attr = table.Entities[slot]
        if not isinstance(attr, TagAttrib):
            continue
        require(
            0 <= attr.Links.OwnerRef < len(table.SlotMap),
            "Generic tag has no live owner reference",
        )
        owner = table.SlotMap[attr.Links.OwnerRef]
        require(
            owner not in result and len(attr.Groups) == 1,
            "Ambiguous saved generic body or face tag",
        )
        result[owner] = attr.Groups[0]
    return result


# Join the generic live BREP body and operation to the reciprocal saved Design owners.
def body_identity(graph, context, model, signed, progenitor, body_tag):
    feature = context.Extrude
    bodies = ResolveField(graph, context.Component, "rBodies", "Bodies")
    serializer = ResolveField(graph, bodies, "rBRepSerializer", "BRepHistorySerializer")
    SameNodes((context.BodyNode,), LinkedNodes(graph, bodies, "children"))
    SameNodes((context.DcBody,), LinkedNodes(graph, context.Fragment, "dcBodies"))
    (member,) = MappingItems(serializer.Fields["mapBodyId"])
    root, secondary = progenitor
    operation = int(body_tag.PrimaryId)
    (occurrence,) = MappingItems(root.Fields["featureTagOccMap"])
    require(
        member.First == signed.journal_solid.EntityTag
        and member.Second == context.BodyNode.ObjectId
        and model.Bodies[0].PartName
        == "Breps.BlobParts/" + serializer.Fields["partName"]
        and graph.Resolve(context.DcBody.Fields["rOwnFeature"]) == feature
        and context.DcBody.Fields["bodyUuid"]
        == context.BodyNode.Fields["persistentId"]
        == root.Fields["bodyUuid"]
        and body_tag == FeatureTag(str(operation), (), secondary, 0)
        and ObjectFields(occurrence.First)["operationId"] == operation
        and feature.Fields["startModelHS"] == signed.history.States[1].StateId
        and feature.Fields["endModelHS"] == signed.journal_solid.StateId,
        "Saved body tag or journal states do not own the linked Design extrusion",
    )
    manager = ResolveField(
        graph, context.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    forward = MappingItems(manager.Fields["featureIdMap"])
    reverse = MappingItems(manager.Fields["enetityIdMap"])
    operations = {row.First: row.Second for row in forward}
    owners = {row.First: SeriesItems(row.Second) for row in reverse}
    require(
        len(operations) == len(forward)
        and len(owners) == len(reverse)
        and set(owners) == {feature.ObjectId, context.SketchFeature.ObjectId}
        and operations
        == {item: owner for owner, entries in owners.items() for item in entries}
        and operations.get(operation) == feature.ObjectId,
        "Native operation map does not reciprocate the history body tag",
    )
    return {
        "operation_id": operation,
        "body_key": member.First,
        "solid": member.Second,
        "body_progenitor": root.ObjectId,
        "secondary_id": secondary,
        "feature": feature.ObjectId,
    }


# A face tag must identify its actual cap plane or the physically selected side.
def check_face_tags(tags, shell, operation, extent, sides, curves):
    areas = face_areas(shell)
    require(
        set(areas) == set(tags),
        "The solid face tag roster differs from the closed topology",
    )
    observed = {}
    for slot, points in areas.items():
        tag = tags[slot]
        name = tag.PrimaryId
        require(
            name not in observed and tag == FeatureTag(name, (operation,), 0, 0),
            "Face tag belongs to another operation or duplicates a face",
        )
        zs = {point[2] for point in points}
        if name in ("1", "2"):
            require(
                zs == {0.0 if name == "1" else extent},
                "Native cap tag leaves its start or end plane",
            )
        else:
            require(
                name in sides
                and zs == {0.0, extent}
                and frozenset((x, y) for x, y, z in points if z == 0.0)
                == curves[sides[name]],
                "Native side tag disagrees with its Design curve and the signed solid",
            )
        observed[name] = sorted(points)
    require(
        set(observed) == {"1", "2", *sides},
        "The saved solid does not bind all six faceted roles",
    )
    return observed


# Join actual edge endpoints in all sketch attributes to their selected Design curve.
def check_sketch_tags(table, curves, extent):
    counts = Counter()
    for slot in table.LiveSlots:
        attr = table.Entities[slot]
        if not isinstance(attr, SketchAttrib):
            continue
        require(
            0 <= attr.Links.OwnerRef < len(table.Entities),
            "Sketch tag has no live owner reference",
        )
        owner = table.Entities[attr.Links.OwnerRef]
        if isinstance(owner, CoedgeNode):
            edge, direction = table.Entities[owner.EdgeRef], 0
        else:
            edge, direction = owner, 1
        require(isinstance(edge, EdgeNode), "Sketch tag has no typed edge owner")
        link = attr.SourceLink
        ends = tuple(
            ReadVertexPoint(table, index)
            for index in (edge.StartVertex, edge.EndVertex)
        )
        require(
            link.PrimaryId in curves
            and link == SketchLink(link.PrimaryId, 0, direction, 1, 1)
            and ends[0][2] == ends[1][2]
            and ends[0][2] in (0.0, extent)
            and frozenset(point[:2] for point in ends) == curves[link.PrimaryId],
            "A native sketch attribute names a different physical curve or direction",
        )
        counts[link.PrimaryId] += 1
    return dict(counts)


# Both separately rooted snapshot sheets must match the original selected profile.
def section_bindings(regions, curves):
    result = []
    for region in regions:
        tags = [link.PrimaryId for link in region.CoedgeTags]
        require(set(tags) == set(curves), "Auxiliary sheet omits a selected curve")
        pairs = zip(
            region.CornersCm, (*region.CornersCm[1:], region.CornersCm[0]), strict=True
        )
        for (start, end), coedge, edge in zip(
            pairs, region.CoedgeTags, region.EdgeTags, strict=True
        ):
            tag = coedge.PrimaryId
            require(
                coedge == SketchLink(tag, 0, 0, 1, 1)
                and edge == SketchLink(tag, 0, 1, 1, 1)
                and frozenset((start[:2], end[:2])) == curves[tag],
                "Auxiliary section curve tag does not identify its saved endpoints",
            )
        result.append(tags)
    return result


# Compare typed signed extent and source geometry with the independent licensed observation.
def compare_measurements(graph, context, signed, witness):
    depth = CheckBinding(graph, context.Along, context)
    taper = CheckBinding(graph, context.Taper, context)
    observed = {item["name"]: item for item in witness["parameters"]}["depth_mm"]
    bounds = signed.evidence["bounds_cm"]
    require(
        depth.Fields["isDriven"] is False
        and depth.Fields["unit"] == "mm"
        and taper.Fields["value"] == 0.0
        and taper.Fields["unit"] == "deg"
        and observed["expression"] == depth.Fields["expression"]
        and isclose(
            observed["value_internal"], signed.extent_cm, rel_tol=0, abs_tol=1e-9
        )
        and isclose(depth.Fields["value"], signed.extent_cm, rel_tol=0, abs_tol=1e-9)
        and witness["body_count"] == 1
        and witness["sketches"][0]["support_name"] == "XY"
        and isclose(
            signed.journal_solid.VolumeCm3 * 1000,
            witness["volume_mm3"],
            rel_tol=0,
            abs_tol=1e-7,
        )
        and all(
            isclose(value * 10, expected, rel_tol=0, abs_tol=1e-7)
            for value, expected in zip(
                (*bounds[0], *bounds[1], *signed.centroid_cm),
                (
                    *witness["bodies"][0]["bounding_box_mm"][0],
                    *witness["bodies"][0]["bounding_box_mm"][1],
                    *witness["center_of_mass_mm"],
                ),
                strict=True,
            )
        ),
        "Saved signed Boss geometry or owned depth differs from licensed readback",
    )
    return {
        "native_expression": depth.Fields["expression"],
        "bbox_mm": witness["bodies"][0]["bounding_box_mm"],
        "volume_mm3": witness["volume_mm3"],
        "centroid_mm": witness["center_of_mass_mm"],
    }


# The generic wire decoder accepts a changed secondary ID but the Design join must reject it.
def corrupt_owner(
    history_bytes, snapshot_bytes, signed, graph, context, model, progenitor
):
    table, shell = signed.journal_table, signed.journal_solid
    original = face_and_body_tags(table)[shell.BodyRef]
    (slot,) = [
        index
        for index, item in enumerate(signed.history.Entities)
        if isinstance(item, TagAttrib)
        and item.Links.OwnerRef == shell.BodyRef
        and item.Groups == (original,)
    ]
    entities = list(signed.history.Entities)
    entities[slot] = replace(
        entities[slot],
        Groups=(replace(original, SecondaryId=original.SecondaryId + 1),),
    )
    changed = EmitJournal(replace(signed.history, Entities=tuple(entities)))
    decoded = read_signed_prism(changed, snapshot_bytes)
    tags = face_and_body_tags(decoded.journal_table)
    require(
        changed != history_bytes
        and decoded.evidence["bounds_cm"] == signed.evidence["bounds_cm"],
        "Owner mutation did not preserve wire geometry",
    )
    return refusal(
        lambda: body_identity(
            graph,
            context,
            model,
            decoded,
            progenitor,
            tags[decoded.journal_solid.BodyRef],
        ),
        "Saved body tag or journal states do not own the linked Design extrusion",
    )


# Retain the exact scope and record attribution before checking the licensed comparison.
def compare_case(raw, digest, variant, witness):
    require(sha256(raw) == digest, "Pinned signed P03 archive digest differs")
    model = ReadDocument(raw)
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    CheckScopes(graph, context, model.Asset.AssetId)
    CheckMatrix(graph, context)
    CheckExtrusion(graph, context)
    CheckSceneRefs(graph, model.Graphics)
    history_bytes, snapshot_bytes = body_parts(raw, model)
    signed = read_signed_prism(history_bytes, snapshot_bytes)
    curves, sides, progenitor = design_curves(graph, context, model.Asset.AssetId)
    journal_tags = face_and_body_tags(signed.journal_table)
    body_tag = journal_tags.pop(signed.journal_solid.BodyRef)
    identity = body_identity(graph, context, model, signed, progenitor, body_tag)
    journal_faces = check_face_tags(
        journal_tags,
        signed.journal_solid,
        identity["operation_id"],
        signed.extent_cm,
        sides,
        curves,
    )
    snapshot_faces = check_face_tags(
        face_and_body_tags(signed.snapshot_table),
        signed.snapshot_solid,
        identity["operation_id"],
        signed.extent_cm,
        sides,
        curves,
    )
    require(
        journal_faces == snapshot_faces,
        "Physical face tags differ between history and snapshot",
    )
    journal_links = check_sketch_tags(signed.journal_table, curves, signed.extent_cm)
    snapshot_links = check_sketch_tags(signed.snapshot_table, curves, signed.extent_cm)
    require(
        journal_links == dict.fromkeys(curves, 2)
        and snapshot_links == dict.fromkeys(curves, 6),
        "The saved sketch link inventories are incomplete",
    )
    result = {
        "source_archive_sha256": digest,
        "packaged_history_type": type(model.Bodies[0].History).__name__,
        "packaged_snapshot_type": type(model.Snapshots[0].Snapshot).__name__,
        **signed.evidence,
        "design_owner": identity,
        "side_curve_labels": sides,
        "world_faces_cm": journal_faces,
        "journal_sketch_link_counts": journal_links,
        "snapshot_sketch_link_counts": snapshot_links,
        "auxiliary_curve_tags_in_saved_order": section_bindings(signed.regions, curves),
        "licensed_geometry": compare_measurements(graph, context, signed, witness),
    }
    if variant == "direction-negative":
        result["public_strict_refusal"] = refusal(
            lambda: open_document(raw, strict=True), REFUSED[variant][1]
        )
        result["wire_valid_owner_mutation_refusal"] = corrupt_owner(
            history_bytes, snapshot_bytes, signed, graph, context, model, progenitor
        )
    else:
        require(
            len(open_document(raw, strict=True).bodies) == 1,
            "Positive strict control was not preserved",
        )
    return result


# Seal all five observations against the original capture receipt and exact scope.
def report():
    snapshot = GitSnapshot(ROOT)
    data = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(data) == SPECIFICATION_SHA256, "P03 signed specification digest differs"
    )
    specification = snapshot.parse_document(data, SPECIFICATION)
    (recipe,) = [item for item in specification["recipes"] if item["id"] == "P03"]
    receipt, assets, observations = capture(snapshot, recipe, "fusion", specification)
    cases = {}
    for variant, digest in CASES.items():
        asset, (phase, witness) = assets[variant], observations[variant]
        require(
            asset["sha256"] == digest and phase == "same_process_reopen",
            "Unexpected signed source custody or observation phase",
        )
        cases[variant] = compare_case(
            snapshot.blob(REVISION, asset["path"]), digest, variant, witness
        )
    return {
        "schema": 1,
        "source_revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "scope": "Saved generic closed and auxiliary prism evidence for four positive and one negative XY P03 discovery cases",
        "capture": {
            key: receipt[key]
            for key in (
                "receipt",
                "measurements",
                "application_build",
                "qualification_blockers",
            )
        },
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
