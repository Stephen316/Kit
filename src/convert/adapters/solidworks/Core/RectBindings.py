from dataclasses import dataclass as Dataclass
from math import dist as Distance
from typing import TypeAlias

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchLine
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity

# native coordinates in metres are checked against the existing millimetre profile
KPointPair: TypeAlias = tuple[float, float]

# verified source endpoints may differ from the legacy scaled values by roundoff only
KPointToleranceMm = 1e-6


# edge slots retain the canonical neutral direction and the independent source record
@Dataclass(frozen=True, slots=True)
class BoundRectEdge:
    Entity: SketchEntity
    Slots: tuple[int, int]
    Source: SketchLine
    SpanValue: MemberSpan


# closed profile consumers need the existing edge order together with its saved point slots
@Dataclass(frozen=True, slots=True)
class RectBindings:
    Points: tuple[KPointPair, ...]
    Edges: tuple[BoundRectEdge, ...]
    PointEntities: tuple[SketchEntity, ...]


# the five typed point records already own the local geometry needed by the neutral sketch
def ReadMmPoints(Profile: ProfileSketch) -> tuple[KPointPair, ...]:
    Result: list[KPointPair] = []
    for LocalValue in Profile.Geometry["points_metres"]:
        XValue, YValue = LocalValue
        Result.append((XValue * 1000, YValue * 1000))
    return tuple(Result)


# endpoint matching retains a neutral direction even when archived edges run in reverse
def MatchEdgeSlots(
    Geometry: LineGeometry, Source: SketchLine, Points: tuple[KPointPair, ...]
) -> tuple[int, int] | None:
    First, Second = Source["point_indices"]
    Start = Geometry.start.x, Geometry.start.y
    Finish = Geometry.end.x, Geometry.end.y
    for StartSlot, EndSlot in ((First, Second), (Second, First)):
        if (
            Distance(Start, Points[StartSlot]) <= KPointToleranceMm
            and Distance(Finish, Points[EndSlot]) <= KPointToleranceMm
        ):
            return StartSlot, EndSlot
    return None


# existing closed profile identities require a unique match to the actual source perimeter
def BindRectEdge(
    Entity: SketchEntity, Profile: ProfileSketch, Points: tuple[KPointPair, ...]
) -> BoundRectEdge:
    Geometry = Entity.geometry
    if not isinstance(Geometry, LineGeometry) or Entity.construction:
        raise ArchiveError("Closed rectangle entity is not a perimeter line")
    Bound: list[BoundRectEdge] = []
    for Source, SpanValue in zip(
        Profile.Geometry["lines"], Profile.Members.Lines, strict=True
    ):
        if Source["native_id"] < 0:
            continue
        Slots = MatchEdgeSlots(Geometry, Source, Points)
        if Slots is not None:
            Bound.append(BoundRectEdge(Entity, Slots, Source, SpanValue))
    RequireArch(len(Bound), 1, "unique typed rectangle edge per neutral entity")
    return Bound[0]


# the original marker identity belongs to a point when its span lies inside the typed member
def BindPointRef(
    Entities: tuple[SketchEntity, ...], SpanValue: MemberSpan, StreamName: str
) -> SketchEntity:
    Found = [
        Entity
        for Entity in Entities
        if Entity.kind in ("point", "native")
        and Entity.provenance is not None
        and any(
            SourceSpan.stream == StreamName
            and SpanValue.Offset <= SourceSpan.offset < SpanValue.EndOffset
            for SourceSpan in Entity.provenance.spans
        )
    ]
    RequireArch(len(Found), 1, "unique neutral point entity for its typed member")
    return Found[0]


# typed vertex identity must corroborate the same loop used by downstream feature consumers
def BindRectangle(
    Neutral: Sketch, Profile: ProfileSketch, StreamName: str
) -> RectBindings:
    RequireArch(len(Neutral.closed_profile_entity_ids), 1, "one neutral rectangle loop")
    (LoopValue,) = Neutral.closed_profile_entity_ids
    RequireArch(len(LoopValue), 4, "four existing rectangle IDs")
    EntityMap = {Entity.id: Entity for Entity in Neutral.entities}
    Points = ReadMmPoints(Profile)
    RequireArch(len(Points), len(Profile.Members.Points), "typed point span inventory")
    Edges = tuple(
        BindRectEdge(EntityMap[EntityId], Profile, Points) for EntityId in LoopValue
    )
    RequireArch(
        len({EdgeValue.Source["native_id"] for EdgeValue in Edges}),
        4,
        "unique typed perimeter IDs",
    )
    RequireArch(
        all(
            EdgeValue.Slots[1] == Following.Slots[0]
            for EdgeValue, Following in zip(Edges, Edges[1:] + Edges[:1], strict=True)
        ),
        True,
        "saved point slots corroborate the neutral loop",
    )
    PointEntities = tuple(
        BindPointRef(Neutral.entities, SpanValue, StreamName)
        for SpanValue in Profile.Members.Points
    )
    RequireArch(
        len({Entity.id for Entity in PointEntities}),
        len(PointEntities),
        "distinct typed point entity IDs",
    )
    return RectBindings(Points, Edges, PointEntities)
