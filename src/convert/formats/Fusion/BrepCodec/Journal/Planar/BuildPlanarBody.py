from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.CheckEdgeUses import CheckEdgeUses
from convert.formats.Fusion.BrepCodec.Journal.Planar.CheckLineEdge import CheckLineEdge
from convert.formats.Fusion.BrepCodec.Journal.Planar.CheckPlanarRing import (
    CheckPlanarRing,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    CrossProduct,
    DotProduct,
)


def BuildPlanarBody(Table: LiveTable, BodyRef: int) -> PlanarShell:
    Faces = ReadBodyFaces(Table, BodyRef)
    CheckEdgeUses(Table, Faces)
    VertexRefs = tuple(
        sorted(
            {
                Value.StartVertex
                for FaceValue in Faces
                for Value in FaceValue.BoundaryUses
            }
        )
    )
    Points = tuple(ReadVertexPoint(Table, Value) for Value in VertexRefs)
    Rings = tuple(
        tuple(VertexRefs.index(Value.StartVertex) for Value in FaceValue.BoundaryUses)
        for FaceValue in Faces
    )
    Edges = {Value.EdgeRef for FaceValue in Faces for Value in FaceValue.BoundaryUses}
    if len(VertexRefs) - len(Edges) + len(Faces) != 2:
        raise ValueError("Fusion convex solid violates its Euler characteristic")
    for EdgeRef in Edges:
        CheckLineEdge(Table, EdgeRef)
    Volume = 0.0
    for FaceValue, Indices in zip(Faces, Rings, strict=True):
        Boundary = tuple(Points[Index] for Index in Indices)
        CheckPlanarRing(FaceValue, Boundary, Points)
        Volume += sum(
            DotProduct(Boundary[0], CrossProduct(Boundary[Index], Boundary[Index + 1]))
            / 6.0
            for Index in range(1, len(Boundary) - 1)
        )
    if not IsFinite(Volume) or Volume <= 1e-12:
        raise ValueError("Fusion closed planar body has no positive volume")
    BodyValue = RequireLive(Table, BodyRef, BodyNode)
    return PlanarShell(
        Table.StateId,
        BodyRef,
        BodyValue.Prefix.EntityTag,
        VertexRefs,
        Points,
        tuple(Value.FaceRef for Value in Faces),
        Rings,
        Volume,
    )
