from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector

KPoint = tuple[float, float]
KSlots = tuple[int, int]
KLocalPairs = ((0, 3), (0, 2), (2, 1), (3, 1))
KFrontAxes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
KRightAxes = ((0, 0, -1), (0, 1, 0), (1, 0, 0))


# canonical target slot order and original neutral endpoint order remain distinguishable
@Dataclass(frozen=True, slots=True)
class LocalEdge:
    Identity: int
    SourceId: str
    PointSlots: KSlots
    SourceSlots: KSlots


# native creation slots are assigned to logical corners before any archive allocation
@Dataclass(frozen=True, slots=True)
class LocalProfile:
    SketchId: str
    Plane: Transform
    AxisCode: int
    CornersMm: tuple[KPoint, ...]
    Edges: tuple[LocalEdge, ...]
    OriginId: str

    @property
    def CornersMetres(self) -> tuple[KPoint, ...]:
        return tuple((X / 1000.0, Y / 1000.0) for X, Y in self.CornersMm)

    @property
    def EdgeSlots(self) -> dict[int, KSlots]:
        return {Edge.Identity: Edge.PointSlots for Edge in self.Edges}


def Axes(Vector: SpaceVector) -> tuple[float, float, float]:
    return Vector.x, Vector.y, Vector.z


# the two supported datums are defined by their physical frame and absence of external support
def RequireDatum(Plane: SupportPlane) -> int:
    Frame = Plane.transform
    Vectors = tuple(Axes(Axis) for Axis in (Frame.x_axis, Frame.y_axis, Frame.z_axis))
    RequireArch(
        Plane.support_selection_id is None
        and Plane.offset_parameter_id is None
        and Axes(Frame.origin) == (0, 0, 0)
        and Vectors in (KFrontAxes, KRightAxes),
        True,
        "origin Front or Right datum with no attached support",
    )
    return 3 if Vectors == KFrontAxes else 1


# only real perimeter edges and one fixed origin reference belong to this profile
def ReadPerimeter(SketchValue: Sketch) -> tuple[dict[str, tuple[KPoint, KPoint]], str]:
    Lines: dict[str, tuple[KPoint, KPoint]] = {}
    Origins: list[str] = []
    for Entity in SketchValue.entities:
        Geometry = Entity.geometry
        if (
            isinstance(Geometry, LineGeometry)
            and not Entity.construction
            and not Entity.fixed
        ):
            Lines[Entity.id] = (
                (Geometry.start.x, Geometry.start.y),
                (Geometry.end.x, Geometry.end.y),
            )
        elif (
            isinstance(Geometry, PointGeometry)
            and Entity.construction
            and Entity.fixed
            and (Geometry.point.x, Geometry.point.y) == (0, 0)
        ):
            Origins.append(Entity.id)
        else:
            raise ValueError(f"{Entity.id} is outside the anchored rectangle profile")
    RequireArch(
        len(SketchValue.entities) == 5 and len(Origins) == 1 and len(Lines) == 4,
        True,
        "four free perimeter lines and one distinct fixed origin",
    )
    RequireArch(Origins[0] in Lines, False, "separate origin identity")
    (Loop,) = SketchValue.closed_profile_entity_ids
    RequireArch(
        len(Loop) == 4 and set(Loop) == set(Lines),
        True,
        "sole declared perimeter over all four lines",
    )
    RequireArch(
        all(
            len(set(Lines[First]) & set(Lines[Second])) == 1
            for First, Second in zip(Loop, Loop[1:] + Loop[:1], strict=True)
        ),
        True,
        "declared closed perimeter order",
    )
    return Lines, Origins[0]


# assign stable fresh target IDs from corner roles and the supported native orientation
def ReadLocalProfile(SketchValue: Sketch, Plane: SupportPlane) -> LocalProfile:
    RequireArch(len(SketchValue.closed_profile_entity_ids), 1, "one selected rectangle")
    AxisCode = RequireDatum(Plane)
    Lines, Origin = ReadPerimeter(SketchValue)
    Points = {Point for Line in Lines.values() for Point in Line}
    RequireArch(
        len(Points) == 4
        and (0, 0) in Points
        and all(IsFinite(Coordinate) for Point in Points for Coordinate in Point),
        True,
        "four finite anchored perimeter corners",
    )
    Ys = {Y for _, Y in Points if Y != 0}
    Xs = {X for X, _ in Points if X != 0}
    RequireArch(len(Xs) == len(Ys) == 1, True, "axis-aligned rectangle")
    (X,), (Y,) = Xs, Ys
    RequireArch(
        Y > 0 and (X > 0 if AxisCode == 3 else X < 0), True, "principal extent signs"
    )
    Corners = ((0.0, 0.0), (X, Y), (0.0, Y), (X, 0.0))
    RequireArch(set(Corners), Points, "complete rectangular corners")
    Slots = {Point: Index for Index, Point in enumerate(Corners)}
    Directed = {
        Name: (Slots[Start], Slots[End]) for Name, (Start, End) in Lines.items()
    }
    Edges = []
    for Index, Pair in enumerate(KLocalPairs, 1):
        Matching = [
            LocalEdge(Index, Name, Pair, Source)
            for Name, Source in Directed.items()
            if set(Source) == set(Pair)
        ]
        RequireArch(len(Matching), 1, "one neutral line per native-local edge")
        Edges.extend(Matching)
    return LocalProfile(
        SketchValue.id, Plane.transform, AxisCode, Corners, tuple(Edges), Origin
    )
