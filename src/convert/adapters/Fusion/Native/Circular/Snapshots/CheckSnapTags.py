from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode

from dataclasses import replace as CopyData

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags


def CheckSnapTags(
    State: GeometryState,
    SolidFaces: tuple[FaceNode, ...],
    Sketch: SketchLink,
    TagSet: TopologyTags | None,
) -> None:
    SolidIds = {
        Index for Index, Entity in enumerate(State.Entities) if Entity in SolidFaces
    }
    SolidEdges = {
        Entity.EdgeRef
        for Entity in State.Entities
        if isinstance(Entity, CoedgeNode)
        and SnapEntity(State, Entity.OwnerLoop, LoopNode).OwnerFace in SolidIds
    }
    Expected: dict[int, FeatureTag | SketchLink] = {}
    for Index, Entity in enumerate(State.Entities):
        if isinstance(Entity, FaceNode) and Index in SolidIds and TagSet is not None:
            Surface = State.Entities[Entity.Surface]
            Expected[Index] = (
                TagSet.SideFace
                if isinstance(Surface, ConeNode)
                else TagSet.BottomFace if Entity.Reversed else TagSet.TopFace
            )
        elif isinstance(Entity, EdgeNode):
            Curve = SnapEntity(State, Entity.CurveRef, EllipseNode)
            Expected[Index] = (
                (TagSet.TopEdge if Curve.Normal[2] < 0 else TagSet.BottomEdge)
                if Index in SolidEdges and TagSet is not None
                else CopyData(Sketch, Direction=1)
            )
        elif isinstance(Entity, CoedgeNode):
            EdgeValue = SnapEntity(State, Entity.EdgeRef, EdgeNode)
            Curve = SnapEntity(State, EdgeValue.CurveRef, EllipseNode)
            if Entity.EdgeRef not in SolidEdges or Curve.Normal[2] > 0:
                Expected[Index] = Sketch
    CheckAttribsMut(State, Expected)


def CheckAttribsMut(
    State: GeometryState, Expected: dict[int, FeatureTag | SketchLink]
) -> None:
    for Entity in State.Entities:
        if isinstance(Entity, TagAttrib):
            Value = Expected.pop(Entity.Links.OwnerRef, None)
            if not isinstance(Value, FeatureTag) or Entity.Groups != (Value,):
                raise ValueError(
                    "Native snapshot feature tag disagrees with modeled topology"
                )
        elif isinstance(Entity, SketchAttrib):
            Value = Expected.pop(Entity.Links.OwnerRef, None)
            if not isinstance(Value, SketchLink) or Entity.SourceLink != Value:
                raise ValueError(
                    "Native snapshot sketch tag disagrees with profile identity"
                )
    if Expected:
        raise ValueError("Native snapshot is missing required topology identities")
