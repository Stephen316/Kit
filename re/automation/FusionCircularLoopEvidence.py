# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import tau

from PairedCaptureIntake import require, sha256
from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.AssetCodec.Zip.ZipLimits import KMaxMemberBytes
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.Profiles.ProfileRef import KLoopGuid, KProfileGuid
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCircular import (
    CheckCircular,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from interchange.geometry.Models.GeometryCurves import CircleGeometry


def design_node(segment, known_classes, identity, class_name):
    records = [row for row in segment.Records if row.ObjectId == identity]
    (primary,) = [row for row in records if row.IsPrimary]
    guid = primary.Groups[0].ClassGuid.upper()
    require(
        known_classes.get(guid) == class_name,
        f"Design object {identity} is not the expected {class_name}",
    )
    return NativeNode(
        segment.Metadata.Header.SegmentId,
        identity,
        class_name,
        tuple(group for row in records for group in row.Groups),
        primary.Frame,
    )


def native_identity(projected):
    origin = projected.provenance
    require(
        origin is not None and origin.native_id.isdecimal(),
        "Projection lacks an exact Design identity",
    )
    return int(origin.native_id)


def provenance(projected):
    return [
        {
            "stream": span.stream,
            "offset": span.offset,
            "length": span.length,
            "record_kind": span.record_kind,
        }
        for span in projected.provenance.spans
    ]


def check_design(model, sketch, feature, circle, dimension_id):
    require(
        isinstance(circle.geometry, CircleGeometry),
        "Projected perimeter lacks a circle geometry",
    )
    (segment,) = [row for row in model.Segments if row.Metadata.Header.SegmentId == 0]
    classes = {row.Value.ClassGuid.upper(): row.NameValue for row in ReadNames()}
    sketch_id, feature_id, curve_id = map(native_identity, (sketch, feature, circle))
    sketch_node = design_node(segment, classes, sketch_id, "MSketch")
    feature_node = design_node(segment, classes, feature_id, "DcSketch")
    curve_node = design_node(segment, classes, curve_id, "CircArc3D")
    fields = curve_node.Fields
    center = fields["rCenterPoint"]
    require(isinstance(center, LocalRef), "Circle has no typed center point reference")
    center_node = design_node(segment, classes, center.ObjectId, "Point3D")
    members = tuple(LocalRef(native_identity(entity)) for entity in sketch.entities) + (
        LocalRef(dimension_id),
    )
    saved_members = SeriesItems(sketch_node.Fields["children"])
    require(
        sketch_node.Fields["rDcNode"] == LocalRef(feature_id)
        and feature_node.Fields["rSketch"] == LocalRef(sketch_id)
        and fields["rParent"] == center_node.Fields["rParent"] == LocalRef(sketch_id)
        and center in members
        and len(saved_members) == len(members)
        and frozenset(saved_members) == frozenset(members)
        and SeriesItems(sketch_node.Fields["dimensions"]) == (LocalRef(dimension_id),),
        "Saved circle, center, dimension and sketch-feature ownership disagree",
    )
    primary_guids = {
        row.Groups[0].ClassGuid.upper() for row in segment.Records if row.IsPrimary
    }
    require(
        not ({KProfileGuid, KLoopGuid} & primary_guids),
        "Sketch-only control has a native feature-selected profile record",
    )
    carrier = ObjectFields(fields["arcCurve"])
    interval = [carrier["startAngle"], carrier["endAngle"]]
    center_coordinates = PointCoords(carrier["center"])
    require(
        fields["rStartPoint"] is None
        and fields["rEndPoint"] is None
        and interval == [0.0, tau]
        and PointCoords(carrier["normal"]) == (0.0, 0.0, 1.0)
        and PointCoords(carrier["refVec"]) == (1.0, 0.0, 0.0)
        and not circle.construction
        and center_coordinates == PointCoords(center_node.Fields["point"])
        and tuple(value * 10.0 for value in center_coordinates)
        == (circle.geometry.center.x, circle.geometry.center.y, 0.0)
        and NumberValue(carrier["radius"]) * 10.0 == circle.geometry.radius,
        "Design carrier is missing a full-turn circle or its exact center",
    )
    return CircleShape(curve_node, center_node, sketch.entities, circle.geometry), {
        "sketch_object_id": sketch_id,
        "feature_object_id": feature_id,
        "curve_object_id": curve_id,
        "center_object_id": center.ObjectId,
        "dimension_object_id": dimension_id,
        "curve_tag": CurveTag(curve_node),
        "angular_interval_rad": interval,
        "feature_selected_profile_records": False,
        "sketch_spans": provenance(sketch),
        "feature_spans": provenance(feature),
        "curve_spans": provenance(circle),
    }


def saved_circle_loop(payload, model, sketch, feature, circle, dimension_id):
    shape, design = check_design(model, sketch, feature, circle, dimension_id)
    require(
        not model.Bodies and len(model.Snapshots) == 1,
        "Expected exactly one sketch-only snapshot",
    )
    stored = model.Snapshots[0]
    state = stored.Snapshot
    require(isinstance(state, GeometryState), "Missing typed sketch topology")
    CheckCircular(model, shape, None, None)
    (loop_id,) = [
        index for index, node in enumerate(state.Entities) if isinstance(node, LoopNode)
    ]
    loop = state.Entities[loop_id]
    coedge = state.Entities[loop.FirstCoedge]
    require(isinstance(coedge, CoedgeNode), "Saved loop does not resolve to one coedge")
    edge = state.Entities[coedge.EdgeRef]
    require(isinstance(edge, EdgeNode), "Saved coedge lacks its typed edge")
    attributes = {
        node.Links.OwnerRef: node.SourceLink
        for node in state.Entities
        if isinstance(node, SketchAttrib)
    }
    require(
        coedge.OwnerLoop == loop_id
        and coedge.NextCoedge == coedge.PriorCoedge == loop.FirstCoedge
        and edge.OwnerCoedge == loop.FirstCoedge
        and edge.StartVertex == edge.EndVertex
        and set(attributes) == {loop.FirstCoedge, coedge.EdgeRef},
        "Saved sheet does not retain one reciprocal full-circle loop",
    )
    member_name = KAssetPrefix + stored.Name
    with OpenFusionZip(payload) as archive:
        member = archive.ReadMember(member_name, KMaxMemberBytes)
    return {
        "scope": "saved sketch sheet membership",
        "native_profile_loop_readback": "unavailable",
        "design": design,
        "snapshot": {
            "member": member_name,
            "sha256": sha256(member),
            "size_bytes": len(member),
            "entity_count": len(state.Entities),
            "face_ordinal": loop.OwnerFace,
            "loop_ordinal": loop_id,
            "coedge_ordinal": loop.FirstCoedge,
            "edge_ordinal": coedge.EdgeRef,
            "seam_vertex_ordinal": edge.StartVertex,
            "angular_interval_rad": [edge.StartParam, edge.EndParam],
            "coedge_sketch_direction": attributes[loop.FirstCoedge].Direction,
            "edge_sketch_direction": attributes[coedge.EdgeRef].Direction,
        },
    }
