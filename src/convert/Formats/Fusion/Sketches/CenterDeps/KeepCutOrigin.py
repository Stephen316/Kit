from dataclasses import replace as Replace

from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.CenterDeps.OriginPoint import ReadOriginPoint
from convert.Formats.Fusion.Sketches.CenterDeps.ReadOriginProj import ReadOriginProj
from convert.Formats.Fusion.Sketches.SketchRuleScope import (
    IndexRuleEnts,
    ReadSketchRoot,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmPoints import IsAsmNear
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector


# source identity and projection geometry together distinguish the authored center datum
def KeepCutOrigin(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Frame: SupportPlane,
    BodyId: int,
    ComponentId: int,
) -> SketchEntity:
    SketchRoot = ReadSketchRoot(SketchValue, Owners)
    Route = ReadOriginProj(BulkData, Owners, SketchRoot.ObjectId, BodyId)
    Entities = IndexRuleEnts(BulkData, Owners, SketchValue, SketchRoot.ObjectId)
    Output = Entities.get(Route.OutputId)
    if (
        Output is None
        or Output.provenance is None
        or not isinstance(Output.geometry, PointGeometry)
        or Output.attributes.get("fusion.entity_genesis") != 0
        or (Output.geometry.point.x, Output.geometry.point.y) != (0.0, 0.0)
    ):
        raise ValueError("Fusion projected origin lacks its owned point cache")
    ContainerId = ReadOriginPoint(BulkData, Owners, Route.SourceId, ComponentId)
    AxisValue = Frame.transform.z_axis
    Origin = Frame.transform.origin
    Residual = OffsetVector(Origin, AxisValue, -DotVector(Origin, AxisValue))
    if not IsAsmNear(Residual, SpaceVector(0.0, 0.0, 0.0)):
        raise ValueError("Fusion projected origin is outside the saved frame")
    Spans = tuple(
        ParamOrigin(Owners[Identity]).spans[0]
        for Identity in (*Route.Records, ContainerId, ComponentId)
    )
    return Replace(
        Output,
        provenance=Replace(Output.provenance, spans=Output.provenance.spans + Spans),
        attributes=FreezeMapping(
            {
                **Output.attributes,
                "fusion.projection_mode": "origin_project",
                "fusion.projection_source_object_id": Route.SourceId,
            }
        ),
    )
