from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode


def CheckCoverage(State: GeometryState) -> None:
    Edges = tuple(Entity for Entity in State.Entities if isinstance(Entity, EdgeNode))
    Vertices = tuple(
        Entity for Entity in State.Entities if isinstance(Entity, VertexNode)
    )
    Faces = tuple(Entity for Entity in State.Entities if isinstance(Entity, FaceNode))
    Expected = (
        ({Entity.CurveRef for Entity in Edges}, EntityIndices(State, EllipseNode)),
        ({Entity.StartVertex for Entity in Edges}, EntityIndices(State, VertexNode)),
        ({Entity.PointRef for Entity in Vertices}, EntityIndices(State, PointNode)),
        (
            {Entity.Surface for Entity in Faces},
            EntityIndices(State, PlaneNode) | EntityIndices(State, ConeNode),
        ),
    )
    if any(Actual != Required for Actual, Required in Expected):
        raise ValueError(
            "Native circular snapshot has unaccounted carriers or endpoints"
        )


def EntityIndices(State: GeometryState, ClassType: type[object]) -> set[int]:
    return {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, ClassType)
    }
