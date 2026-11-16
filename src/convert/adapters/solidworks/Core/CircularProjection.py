# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from math import pi as PiValue, sqrt as SquareRoot
from struct import error as StructError

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.CircularSketch import (
    BindRoundParam,
    BindRoundSketch,
    BindRoundPlane,
    CircularSource,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.CircularPartition import (
    CircularShape,
    ReadRoundPart,
)
from convert.adapters.solidworks.Core.Scope.ScopeDocument import KScopeUnresolved
from convert.adapters.solidworks.Resolved.Circular.Part import (
    CircularPart,
    ReadRoundModel,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumDocument import Severity
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import ParameterValue
from interchange.Records.RecordProvenance import ProvenanceSpan
from interchange.Records.RecordTopology import TopologyCounts
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorSpace import SpaceVector


# leave established readers in charge outside the selected ordinary single circle candidate
def IsCircleRead(Document: CadDocument, Model: NativeModel, Stream: str) -> bool:
    if (
        Model.cut_source is not None
        or KScopeUnresolved in Model.diagnostics
        or len(Model.sketches) != 1
        or len(Model.operations) != 1
        or len(Document.sketches) != 1
    ):
        return False
    SketchValue, Operation = Model.sketches[0], Model.operations[0]
    return (
        SketchValue.rectangle is None
        and SketchValue.native_stream == Operation.native_stream == Stream
        and Operation.kind == "join"
        and any(
            not Entity.construction and isinstance(Entity.geometry, CircleGeometry)
            for Entity in Document.sketches[0].entities
        )
    )


# reconcile the typed feature identities and publish the positive blind extent with source spans
def BindCircleBoss(
    BossFeature: FeatureStep,
    SketchFeature: FeatureStep,
    Saved: CircularPart,
    Stream: str,
    DepthId: str,
) -> FeatureStep:
    BossValue = Saved.Boss
    Definition = BossFeature.definition
    RequireArch(
        BossFeature.name == BossValue["name"]
        and BossFeature.attributes.get("native_object_id")
        == BossValue["native_feature_id"]
        and BossFeature.kind == FeatureKind.KExtrusion
        and BossFeature.operation == BooleanOp.JOIN
        and BossFeature.order > SketchFeature.order
        and isinstance(Definition, ExtrudeFeature)
        and not BossFeature.suppressed
        and not BossFeature.selection_ids,
        True,
        "public circular boss agrees with the reached single profile extrusion",
    )
    Depth = BossValue["depth_display"]["dimension"]
    EndSpec = BossValue["end_specification"]
    Source = CircularSource(
        Stream,
        str(BossValue["native_feature_id"]),
        (BossValue["offset"], BossValue["boss_end"]),
        "circular-extrusion",
    )
    Spans = (
        ProvenanceSpan(
            Stream, BossValue["profile_ref_offset"], 2, "operation-profile-reference"
        ),
        ProvenanceSpan(
            Stream,
            EndSpec["offset"],
            BossValue["depth_display"]["offset"] - EndSpec["offset"],
            "extrusion-end-spec",
        ),
        ProvenanceSpan(Stream, Depth["value_offset"], 8, "extrusion-depth-scalar"),
    )
    return Replace(
        BossFeature,
        input_feature_ids=(SketchFeature.id,),
        sketch_id=SketchFeature.sketch_id,
        parameter_ids=(DepthId,),
        definition=ExtrudeFeature(
            ParameterValue(BossValue["signed_depth_m"] * 1000, ValueKind.LENGTH, "mm"),
            ExtrudeEnd.BLIND,
            direction=SpaceVector(*BossValue["axis"]),
        ),
        provenance=Replace(Source, spans=(*Source.spans, *Spans)),
    )


# the analytically checked closed cylinder provides body measures in document millimetres
def BindRoundBody(
    BodyValue: DesignBody,
    Saved: CircularPart,
    Shape: CircularShape,
    Feature: FeatureStep,
    PayloadId: str | None,
) -> DesignBody:
    BossValue = Saved.Boss
    AxisValue, Origin = BossValue["axis"], BossValue["start_center_m"]
    Radius, Depth = Shape["radius_m"], BossValue["signed_depth_m"]
    Extents = tuple(
        Radius * SquareRoot(max(0.0, 1 - Direction**2)) for Direction in AxisValue
    )
    Endpoint = tuple(
        First + Depth * Direction
        for First, Direction in zip(Origin, AxisValue, strict=True)
    )
    Lower = SpaceVector(
        *(
            1000 * (min(StartValue, EndValue) - Extent)
            for StartValue, EndValue, Extent in zip(
                Origin, Endpoint, Extents, strict=True
            )
        )
    )
    Upper = SpaceVector(
        *(
            1000 * (max(StartValue, EndValue) + Extent)
            for StartValue, EndValue, Extent in zip(
                Origin, Endpoint, Extents, strict=True
            )
        )
    )
    return Replace(
        BodyValue,
        final_feature_id=Feature.id,
        topology=TopologyCounts(
            solid_count=1,
            shell_count=1,
            face_count=Shape["face_count"],
            edge_count=Shape["edge_count"],
            vertex_count=0,
            volume=Shape["analytic_volume_m3"] * 1e9,
            surface_area=2 * PiValue * Radius * (Radius + Depth) * 1e6,
            bounding_box=BoundingBox(Lower, Upper),
            valid=True,
        ),
        attributes=FreezeMapping(
            {
                **BodyValue.attributes,
                "native_body_id": BossValue["saved_body_id"],
                "native_producer_feature_id": BossValue["native_feature_id"],
                "native_producer_transfer_object": BossValue["transfer_object"],
                "native_partition_owner": Shape["native_owner"],
                "native_partition_region": Shape["native_region"],
                "brep_closed_edge_representative_vertices": Shape[
                    "closed_edge_representative_vertices"
                ],
                "solidworks.body_centroid_mm": tuple(
                    Value * 1000 for Value in BossValue["centroid_m"]
                ),
                **(
                    {"parasolid_active_payload_id": PayloadId}
                    if PayloadId is not None
                    else {}
                ),
            }
        ),
    )


# match the selected payload by stream and digest before exposing the decoded native solid
def LinkRoundBrep(
    Document: CadDocument,
    Geometry: BrepModel,
    BodyId: str,
    Shape: CircularShape,
    IncludeBrep: bool,
) -> tuple[BrepModel | None, str | None]:
    if not IncludeBrep:
        return None, None
    (Payload,) = tuple(
        Value
        for Value in Document.brep_payloads
        if Value.source_stream == Shape["stream"]
        and Value.kind == "partition"
        and Value.sha256 == Shape["payload_sha256"]
    )
    (Carrier,) = Geometry.bodies
    RequireArch(
        Carrier.design_body_id in ("", BodyId),
        True,
        "unambiguous circular partition design body",
    )
    Attached = Replace(Geometry, bodies=(Replace(Carrier, design_body_id=BodyId),))
    RequireArch(
        Attached.validate(frozenset({BodyId})),
        (),
        "valid owned active cylindrical partition",
    )
    return Attached, Payload.id


# replace all editing and ownership records atomically after checking their existing identities
def BuildRoundDoc(
    Document: CadDocument,
    Saved: CircularPart,
    Stream: str,
    Geometry: BrepModel,
    Shape: CircularShape,
    IncludeBrep: bool,
) -> CadDocument:
    (SketchValue,), (BodyValue,) = Document.sketches, Document.bodies
    Reached = {
        Saved.Profile["feature_id"],
        Saved.Boss["native_feature_id"],
        Saved.Origin.FeatureId,
        Saved.Datum.FeatureId,
    }
    Records = tuple(
        Value
        for Value in Document.feature_timeline
        if Value.attributes.get("native_object_id") in Reached
    )
    Features = {Value.attributes.get("native_object_id"): Value for Value in Records}
    RequireArch(
        len(Records) == len(Features) == len(Reached) == 4,
        True,
        "unique reached circular feature identities",
    )
    SketchFeature = Features[Saved.Profile["feature_id"]]
    BossFeature = Features[Saved.Boss["native_feature_id"]]
    OriginFeature = Features[Saved.Origin.FeatureId]
    DatumFeature = Features[Saved.Datum.FeatureId]
    RequireArch(
        (
            SketchFeature.name,
            SketchFeature.sketch_id,
            BossFeature.sketch_id,
            OriginFeature.name,
            DatumFeature.name,
        ),
        (
            Saved.Profile["name"],
            SketchValue.id,
            SketchValue.id,
            Saved.Origin.NameValue,
            Saved.Datum.NameValue,
        ),
        "public circular sketch, boss, datum and Origin match their archive identities",
    )
    RequireArch(
        BodyValue.final_feature_id,
        BossFeature.id,
        "circular boss owns the public design body",
    )
    RequireArch(
        OriginFeature.order < SketchFeature.order
        and DatumFeature.order < SketchFeature.order,
        True,
        "circular sketch owns earlier support references",
    )
    (Plane,) = tuple(
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    Support = BindRoundPlane(Plane, Saved, Stream)
    Radial, Extent = Saved.Diameter, Saved.Boss["depth_display"]["dimension"]
    Diameter = BindRoundParam(
        Document.parameters,
        SketchFeature.id,
        Radial["parameter_name"],
        Radial["diameter_m"],
        Stream,
        Radial["parameter_offset"],
        Radial["native_id"],
        "sketch-diameter-scalar",
    )
    Depth = BindRoundParam(
        Document.parameters,
        BossFeature.id,
        Extent["parameter_name"],
        Extent["metres"],
        Stream,
        Extent["value_offset"],
        Extent["native_dimension_id"],
        "extrusion-depth-scalar",
    )
    RequireArch(
        (SketchFeature.parameter_ids, BossFeature.parameter_ids),
        ((Diameter.id,), (Depth.id,)),
        "exact circular profile and boss driving parameter roster",
    )
    Sketch = BindRoundSketch(SketchValue, Saved, Diameter.id, Stream)
    BossStep = BindCircleBoss(BossFeature, SketchFeature, Saved, Stream, Depth.id)
    SketchStep = Replace(
        SketchFeature,
        input_feature_ids=(DatumFeature.id, OriginFeature.id),
        provenance=Sketch.provenance,
    )
    BrepValue, PayloadId = LinkRoundBrep(
        Document, Geometry, BodyValue.id, Shape, IncludeBrep
    )
    Revisions = {BossStep.id: BossStep, SketchStep.id: SketchStep}
    Parameters = {Diameter.id: Diameter, Depth.id: Depth}
    Result = Replace(
        Document,
        support_planes=tuple(
            Support if Value is Plane else Value for Value in Document.support_planes
        ),
        sketches=(Sketch,),
        feature_timeline=tuple(
            Revisions.get(Value.id, Value) for Value in Document.feature_timeline
        ),
        parameters=tuple(
            Parameters.get(Value.id, Value) for Value in Document.parameters
        ),
        bodies=(BindRoundBody(BodyValue, Saved, Shape, BossStep, PayloadId),),
        brep=BrepValue,
    )
    Result.assert_valid()
    return Result


# a contradiction retains the reader s existing compatibility document and a scoped diagnostic
def ProjectRoundDoc(
    Document: CadDocument,
    Native: NativeModel,
    Archive: SldprtArchive,
    IncludeBrep: bool,
) -> CadDocument:
    ConfigId = Native.active_configuration_id
    if ConfigId is None:
        return Document
    Config = f"Contents/Config-{ConfigId}"
    Stream = f"{Config}-ResolvedFeatures"
    if (
        not IsCircleRead(Document, Native, Stream)
        or ContainerMo(Archive.streams) != KConfigGen
    ):
        return Document
    try:
        Saved = ReadRoundModel(
            Archive.require(Config), Archive.require(Stream), KConfigGen
        )
        Geometry, Shape = ReadRoundPart(Archive, Config, Saved.Boss, Saved.Circle)
        return BuildRoundDoc(Document, Saved, Stream, Geometry, Shape, IncludeBrep)
    except (KeyError, IndexError, ValueError, StructError) as ErrorInfo:
        return Replace(
            Document,
            diagnostics=(
                *Document.diagnostics,
                Diagnostic(
                    code="sldprt.circular_projection_unresolved",
                    message=str(ErrorInfo),
                    severity=Severity.INFO,
                ),
            ),
        )
