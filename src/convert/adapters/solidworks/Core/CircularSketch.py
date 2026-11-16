# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from math import isclose as IsClose

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Format import PART_FORMAT_ID as KPartFormatId
from convert.adapters.solidworks.Core.OrdinaryRead import KArchiveSupport
from convert.adapters.solidworks.Resolved.Circular.Part import CircularPart
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# Every typed neutral record keeps the exact producer span within the selected resolved stream.
def CircularSource(Stream: str, NativeId: str, Bounds, Record: str) -> Provenance:
    First, Last = Bounds
    return Provenance(
        KPartFormatId,
        NativeId,
        spans=(ProvenanceSpan(Stream, First, Last - First, Record),),
    )


# Retain stable public parameter IDs once their saved owner, name, and scalar agree.
def BindCircularParameter(
    Parameters: tuple[Parameter, ...],
    Owner: str,
    Name: str,
    Metres: float,
    Stream: str,
    Offset: int,
    Identity: int,
    Record: str,
) -> Parameter:
    (ParameterValueData,) = tuple(
        Value for Value in Parameters if Value.owner_id == Owner and Value.name == Name
    )
    Existing = ParameterValueData.value
    RequireArch(
        ParameterValueData.role == ParameterRole.DRIVING
        and ParameterValueData.expression is None
        and Existing.kind == ValueKind.LENGTH
        and Existing.unit == "mm"
        and type(Existing.value) in (int, float)
        and IsClose(float(Existing.value), Metres * 1000, rel_tol=0, abs_tol=1e-6),
        True,
        "public circular driving parameter agrees with the owned archive scalar",
    )
    NewValue = ParameterValue(Metres * 1000, ValueKind.LENGTH, "mm")
    return Replace(
        ParameterValueData,
        value=NewValue,
        provenance=CircularSource(Stream, str(Identity), (Offset, Offset + 8), Record),
    )


# Rebind the already reached principal support using its typed frame and saved feature span.
def BindCircularSupport(
    Plane: SupportPlane, Saved: CircularPart, Stream: str
) -> SupportPlane:
    Datum = Saved.Datum
    RequireArch(
        (Plane.name, Plane.attributes.get("native_object_id")),
        (Datum.NameValue, Datum.FeatureId),
        "circular support matches the reached public datum",
    )
    Point = SpaceVector(*(Value * 1000 for Value in Datum.Geometry.PointMetres))
    Basis = tuple(SpaceVector(*Direction) for Direction in Saved.Support["axes"])
    return Replace(
        Plane,
        transform=Transform(Point, *Basis),
        provenance=CircularSource(
            Stream,
            str(Datum.FeatureId),
            (Datum.Offset, Datum.EndOffset),
            "sketch-support-plane",
        ),
    )


# Locate the unique retained representation of the typed profile and reconcile its sampled geometry.
def BindCircleEntity(Neutral: Sketch, Saved: CircularPart, Stream: str) -> SketchEntity:
    ((EntityId,),) = Neutral.closed_profile_entity_ids
    (Entity,) = tuple(Value for Value in Neutral.entities if Value.id == EntityId)
    Arc = Saved.Circle
    Center = Saved.Points[Arc["center_slot"]]["xy_m"]
    Geometry = CircleGeometry(
        PlaneVector(*(Value * 1000 for Value in Center)), Arc["radial_metres"] * 1000
    )
    Existing = Entity.geometry
    RequireArch(
        isinstance(Existing, CircleGeometry)
        and not Entity.construction
        and IsClose(Existing.center.x, Geometry.center.x, rel_tol=0, abs_tol=1e-6)
        and IsClose(Existing.center.y, Geometry.center.y, rel_tol=0, abs_tol=1e-6)
        and IsClose(Existing.radius, Geometry.radius, rel_tol=0, abs_tol=1e-6),
        True,
        "sampled circular profile agrees with its typed member",
    )
    return Replace(
        Entity,
        geometry=Geometry,
        kind=GeometryKind.KCircle,
        provenance=CircularSource(
            Stream, str(Arc["native_id"]), Arc["span"], "sketch-profile-circle"
        ),
        attributes=FreezeMapping(
            {
                **Entity.attributes,
                "native_segment_id": Arc["native_id"],
                "native_member_index": Arc["arc_slot"],
                "native_center_slot": Arc["center_slot"],
                "native_seam_slot": Arc["seam_slot"],
            }
        ),
    )


# The fixed construction point represents the actual external Origin handle reached by G2.
def BindOriginProxy(Neutral: Sketch, Saved: CircularPart, Stream: str) -> SketchEntity:
    Reference = Saved.Coincidence["origin_proxy"]
    ((OriginSlot, PointId),) = tuple(
        Item
        for Item in Saved.Coincidence["point_native_ids"]
        if Item[0] != Saved.Circle["center_slot"]
    )
    Point = Saved.Points[OriginSlot]
    return SketchEntity(
        f"{Neutral.id}:origin:{PointId}",
        GeometryKind.KPoint,
        PointGeometry(PlaneVector(*(Value * 1000 for Value in Point["xy_m"]))),
        construction=True,
        fixed=True,
        provenance=CircularSource(
            Stream, str(PointId), Point["span"], "sketch-origin-point"
        ),
        attributes=FreezeMapping(
            {
                "native_point_id": (OriginSlot, PointId),
                "native_origin_feature_id": Reference["feature_id"],
                "native_origin_point_handle": Reference["handle_fields"],
            }
        ),
    )


# Both typed relations are attached together, preserving the original diameter ID and G2 operand order.
def BindCircularSketch(
    Neutral: Sketch, Saved: CircularPart, ParameterId: str, Stream: str
) -> Sketch:
    Profile = Saved.Profile
    RequireArch(
        (Neutral.name, Neutral.attributes.get("native_object_id")),
        (Profile["name"], Profile["feature_id"]),
        "public circular sketch and its typed owner agree",
    )
    Circle = BindCircleEntity(Neutral, Saved, Stream)
    Origin = BindOriginProxy(Neutral, Saved, Stream)
    RequireArch(
        all(Value.id == Circle.id or Value.construction for Value in Neutral.entities),
        True,
        "circular resolved sketch accounts for all public non-construction entities",
    )
    (Diameter,) = Neutral.constraints
    RequireArch(
        (Diameter.kind, Diameter.parameter_id, Diameter.references),
        ("diameter", ParameterId, (ConstraintRef(Circle.id),)),
        "public diameter relation uses the reached circle and owned parameter",
    )
    Data = Saved.Diameter
    Driving = Replace(
        Diameter,
        driving=True,
        provenance=CircularSource(
            Stream, str(Data["native_id"]), Data["span"], "sketch-diameter"
        ),
        attributes=FreezeMapping(
            {
                **Diameter.attributes,
                "native_dimension_id": Data["native_id"],
                "native_parameter_object": Data["parameter_object"],
                "native_arc_handle": Data["arc_handle"],
            }
        ),
    )
    G2 = Saved.Coincidence
    OriginSlot = Origin.attributes["native_point_id"][0]
    Refs = tuple(
        (
            ConstraintRef(Origin.id)
            if Slot == OriginSlot
            else ConstraintRef(Circle.id, "center")
        )
        for Slot in G2["point_indices"]
    )
    Coincidence = SketchRelation(
        f"sldprt:constraint:{Profile['feature_id']}:native-relation:{G2['offset']}",
        "coincident",
        Refs,
        provenance=CircularSource(
            Stream,
            str(G2["offset"]),
            (G2["offset"], G2["end"]),
            "sketch-origin-coincidence",
        ),
        attributes=FreezeMapping(
            {
                "native_code": G2["type_code"],
                "native_point_ids": tuple(G2["point_native_ids"]),
                "native_point_handles": tuple(G2["point_handle_objects"]),
                "native_origin_feature_id": G2["origin_feature"],
            }
        ),
    )
    return Replace(
        Neutral,
        entities=(Circle, Origin),
        constraints=(Driving, Coincidence),
        parameter_ids=(ParameterId,),
        provenance=CircularSource(
            Stream,
            str(Profile["feature_id"]),
            (Profile["feature_start"], Saved.Boss["offset"]),
            "circular-sketch",
        ),
        attributes=FreezeMapping(
            {
                **Neutral.attributes,
                "support_plane_native_id": Saved.Datum.FeatureId,
                "support_plane_source": KArchiveSupport,
                "unframed_support_plane_native_id": None,
            }
        ),
    )
