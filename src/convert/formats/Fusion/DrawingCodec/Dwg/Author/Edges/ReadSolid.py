from collections.abc import Iterable
from typing import TypeVar

from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepEdge, BrepFace, BrepVertex
from interchange.geometry.models.Transform import KTransformIdentity
from interchange.geometry.models.VectorSpace import SpaceVector

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
    IsNear,
    Length,
    Minus,
    UnitVector,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import (
    RoundPoint,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidFaces import (
    KLinkGap,
    MakeFace,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SmoothEdges import (
    CheckSmooth,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    FlatFace,
    KEdgePath,
    KPointTriple,
    LinePath,
    RoundPath,
    SolidEdge,
    SolidShape,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Cross,
    DotProduct,
    Scaled,
)

KItem = TypeVar("KItem")


def KeyedById(Items: Iterable[KItem]) -> dict[str, KItem]:
    return {str(getattr(Entry, "id")): Entry for Entry in Items}


def PointOf(Value: SpaceVector) -> KPointTriple:
    return (Value.x, Value.y, Value.z)


def ShellFaces(Model: BrepModel) -> tuple[BrepFace, ...]:
    if len(Model.bodies) != 1:
        raise ValueError("Authored DWG view solid must hold exactly one body")
    BodyItem = Model.bodies[0]
    if BodyItem.transform != KTransformIdentity:
        raise ValueError("Authored DWG view solid body must not be transformed")
    if len(BodyItem.region_ids) != 1:
        raise ValueError("Authored DWG view solid must hold exactly one region")
    UseIds = KeyedById(Model.regions)[BodyItem.region_ids[0]].shell_use_ids
    if len(UseIds) != 1:
        raise ValueError("Authored DWG view solid must hold exactly one shell")
    ShellId = KeyedById(Model.shell_uses)[UseIds[0]].shell_id
    FaceUses = KeyedById(Model.face_uses)
    Faces = KeyedById(Model.faces)
    return tuple(
        Faces[FaceUses[UseId].face_id]
        for UseId in KeyedById(Model.shells)[ShellId].face_use_ids
    )


def FaceEdges(Model: BrepModel, FaceItem: BrepFace) -> tuple[str, ...]:
    Loops = KeyedById(Model.loops)
    Coedges = KeyedById(Model.coedges)
    return tuple(
        Coedges[CoedgeId].edge_id
        for LoopId in FaceItem.loop_ids
        for CoedgeId in Loops[LoopId].coedge_ids
    )


def WalkIds(Model: BrepModel, Faces: tuple[BrepFace, ...]) -> dict[str, int]:
    Found: dict[str, int] = {}
    for FaceItem in Faces:
        for EdgeKey in FaceEdges(Model, FaceItem):
            _ = Found.setdefault(EdgeKey, len(Found))
    return Found


def CirclePath(
    Curve: CircleCurve, EdgeItem: BrepEdge, Start: KPointTriple, Finish: KPointTriple
) -> RoundPath:
    Normal = UnitVector(PointOf(Curve.axis))
    Reference = PointOf(Curve.reference_direction)
    XAxis = UnitVector(Minus(Reference, Scaled(Normal, DotProduct(Reference, Normal))))
    Lower, Upper = sorted((EdgeItem.start_parameter, EdgeItem.end_parameter))
    IsClosed = EdgeItem.start_vertex_id == EdgeItem.end_vertex_id
    Sweep = KFullTurn if IsClosed else Upper - Lower
    if not 0 < Sweep <= KFullTurn:
        raise ValueError(f"Authored DWG view edge {EdgeItem.id} has a bad arc range")
    Center = PointOf(Curve.center)
    Curved = RoundPath(
        Center, Normal, XAxis, Cross(Normal, XAxis), Curve.radius, Lower, Sweep
    )
    Margin = KLinkGap * max(1.0, Curve.radius)
    Lowest, Highest = RoundPoint(Curved, Lower), RoundPoint(Curved, Upper)
    IsForward = IsNear(Lowest, Start, Margin) and IsNear(Highest, Finish, Margin)
    IsBackward = IsNear(Lowest, Finish, Margin) and IsNear(Highest, Start, Margin)
    if not (IsForward or IsBackward):
        raise ValueError(f"Authored DWG view edge {EdgeItem.id} misses its vertices")
    return RoundPath(
        Center,
        Normal,
        XAxis,
        Cross(Normal, XAxis),
        Curve.radius,
        Lower % KFullTurn,
        Sweep,
    )


def EdgePath(
    Curve: BrepCurve, EdgeItem: BrepEdge, Vertices: dict[str, BrepVertex]
) -> KEdgePath:
    Start = PointOf(Vertices[EdgeItem.start_vertex_id].point)
    Finish = PointOf(Vertices[EdgeItem.end_vertex_id].point)
    if isinstance(Curve, CircleCurve):
        return CirclePath(Curve, EdgeItem, Start, Finish)
    if not isinstance(Curve, LineCurve):
        raise ValueError(
            f"Authored DWG view edges do not cover {type(Curve).__name__} edges"
        )
    Direction = UnitVector(PointOf(Curve.direction))
    for Point in (Start, Finish):
        Offset = Minus(Point, PointOf(Curve.origin))
        if Length(Cross(Offset, Direction)) > KLinkGap * max(1.0, Length(Offset)):
            raise ValueError(f"Authored DWG view edge {EdgeItem.id} leaves its line")
    return LinePath(Start, Finish)


def EdgeOwners(Model: BrepModel, Faces: tuple[BrepFace, ...]) -> dict[str, list[int]]:
    Owners: dict[str, list[int]] = {}
    for FaceIndex, FaceItem in enumerate(Faces):
        for EdgeKey in FaceEdges(Model, FaceItem):
            Owners.setdefault(EdgeKey, []).append(FaceIndex)
    return Owners


def CheckBounds(Model: BrepModel, Lower: KPointTriple, Upper: KPointTriple) -> None:
    for Vertex in Model.vertices:
        if any(
            Value < Lowest - KLinkGap or Value > Highest + KLinkGap
            for Value, Lowest, Highest in zip(PointOf(Vertex.point), Lower, Upper)
        ):
            raise ValueError("Authored DWG view solid lies outside its view bounds")


def EdgePaths(Model: BrepModel, Walked: dict[str, int]) -> dict[str, KEdgePath]:
    Edges = KeyedById(Model.edges)
    Curves = KeyedById(Model.curves)
    Vertices = KeyedById(Model.vertices)
    return {
        EdgeKey: EdgePath(Curves[Edges[EdgeKey].curve_id], Edges[EdgeKey], Vertices)
        for EdgeKey in Walked
        if not Edges[EdgeKey].degenerate
    }


def ReadSolid(Model: BrepModel, Lower: KPointTriple, Upper: KPointTriple) -> SolidShape:
    CheckBounds(Model, Lower, Upper)
    Faces = ShellFaces(Model)
    Walked = WalkIds(Model, Faces)
    Paths = EdgePaths(Model, Walked)
    Surfaces = KeyedById(Model.surfaces)
    Built = tuple(
        MakeFace(
            FaceIndex,
            Surfaces[FaceItem.surface_id],
            tuple(
                Paths[Entry] for Entry in FaceEdges(Model, FaceItem) if Entry in Paths
            ),
        )
        for FaceIndex, FaceItem in enumerate(Faces)
    )
    CheckSmooth(Built, Paths, EdgeOwners(Model, Faces))
    return SolidShape(
        tuple(
            SolidEdge(Walked[EdgeKey], Paths[EdgeKey])
            for EdgeKey in sorted(Paths, key=Walked.__getitem__)
        ),
        tuple(Shape for Shape in Built if isinstance(Shape, FlatFace)),
        tuple(Shape for Shape in Built if not isinstance(Shape, FlatFace)),
    )
