from functools import partial as Partial

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.sketch.Cursor import SketchArchive
from convert.adapters.solidworks.sketch.GeometryTypes import (
    KLineRow,
    KPointId,
    KPointRow,
    KRelationRow,
    KSketchDistance,
    SketchGeometry,
    SketchRelation,
)
from convert.adapters.solidworks.sketch.Members import ReadLineItem, ReadPointMut
from convert.adapters.solidworks.sketch.MemberSpans import MemberSpans, ReadMemberRows
from convert.adapters.solidworks.sketch.Relations import ReadDims, ReadRelations

# the logical relation type selects a sketch local axis only after binding its line
KAxisRelations = {4: "horizontal", 5: "vertical"}


# axis relations must match a unique serialized line within this sketch
def BindRelations(
    Cursor: SketchArchive, Relations: list[KRelationRow], Lines: list[KLineRow]
) -> list[SketchRelation]:
    Records: list[SketchRelation] = []
    Segments = {LineRow[1]: LineRow for LineRow in Lines if LineRow[1] >= 0}
    RequireArch(
        len(Segments),
        sum(LineRow[1] >= 0 for LineRow in Lines),
        "unique line identities",
    )
    for Start, StopValue, Target, TypeValue, Flags in Relations:
        Handle = Cursor.Handles[Target]
        RequireArch(Handle[1:], (-1, 0), "witnessed local relation handle fields")
        RequireArch(
            TypeValue in KAxisRelations, True, "supported one-member relation type"
        )
        Segment = Segments[Handle[0]]
        Records.append(
            {
                "start": Start,
                "end": StopValue,
                "line_handle_object": Target,
                "line_handle_fields": Handle,
                "segment_native_id": Segment[1],
                "type_code": TypeValue,
                "kind": KAxisRelations[TypeValue],
                "scalar_fields": Flags,
            }
        )
    return Records


# a distance remains editable only when both handles resolve local point identities
def BindDimensions(
    Cursor: SketchArchive, Points: list[KPointRow]
) -> list[KSketchDistance]:
    Records: list[KSketchDistance] = []
    for (ClassName, Index, NameValue, Value, First, Second), _ in Cursor.Dimensions:
        Operands: list[KPointId] = []
        for HandleIndex in (First, Second):
            Position, Owner, Flags = Cursor.Handles[HandleIndex]
            RequireArch(
                (Owner, Flags), (-1, 0), "witnessed local dimension handle fields"
            )
            RequireArch(
                0 <= Position < len(Points), True, "dimension point in its sketch"
            )
            Identity, _, _ = Points[Position]
            Operands.append((Position, Identity))
        Records.append(
            {
                "class": ClassName,
                "native_id": Index,
                "name": NameValue,
                "metres": Value,
                "point_handle_objects": [First, Second],
                "point_native_ids": Operands,
            }
        )
    return Records


# geometry stays local while the enclosing profile still owns sketch placement
def BindGeometry(
    Cursor: SketchArchive,
    ObjectIndex: int,
    Start: int,
    Points: list[KPointRow],
    Lines: list[KLineRow],
    Relations: list[KRelationRow],
) -> SketchGeometry:
    return {
        "object_index": ObjectIndex,
        "body_start": Start,
        "geometry_end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
        "points_metres": [Coords for _, _, Coords in Points],
        "point_relation_tallies": [
            {"id": (Position, Identity), "tally": Tally}
            for Position, (Identity, Tally, _) in enumerate(Points)
        ],
        "external_point_references": [
            {"local_id": (Position, Identity), **Cursor.PointReferences[Identity]}
            for Position, (Identity, _, _) in enumerate(Points)
            if Identity in Cursor.PointReferences
        ],
        "lines": [
            {
                "member_index": Index,
                "native_id": Identity,
                "flags": Flags,
                "point_indices": [First, Second],
            }
            for Index, Identity, Flags, First, Second in Lines
        ],
        "length_dimensions": BindDimensions(Cursor, Points),
        "member_relations": BindRelations(Cursor, Relations, Lines),
    }


# the member boundaries survive the geometry handoff to the neutral projection
def ReadGeoSpansMut(
    Cursor: SketchArchive, ObjectIndex: int
) -> tuple[SketchGeometry, MemberSpans]:
    Start = Cursor.Offset
    Cursor.Dimensions.clear()
    Cursor.PointReferences.clear()
    PointCount = Cursor.ReadCount()
    Points, PointSpans = ReadMemberRows(
        Cursor, PointCount, Partial(ReadPointMut, Cursor)
    )
    Lines, LineSpans = ReadMemberRows(
        Cursor, Cursor.ReadCount(), Partial(ReadLineItem, Cursor, PointCount)
    )
    ReadDims(Cursor)
    Relations = ReadRelations(Cursor)
    Distances = tuple(Source for _, Source in Cursor.Dimensions)
    return BindGeometry(
        Cursor, ObjectIndex, Start, Points, Lines, Relations
    ), MemberSpans(PointSpans, LineSpans, Distances)


# research callers can keep their established geometry report shape
def ReadGeometryMut(Cursor: SketchArchive, ObjectIndex: int) -> SketchGeometry:
    Geometry, _ = ReadGeoSpansMut(Cursor, ObjectIndex)
    return Geometry
