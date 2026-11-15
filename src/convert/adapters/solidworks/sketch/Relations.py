from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.sketch.Cursor import SketchArchive
from convert.adapters.solidworks.sketch.DimFields import ReadDimBase, ReadDimFields
from convert.adapters.solidworks.sketch.GeometryTypes import (
    Coincidence,
    KPointId,
    KRelationRow,
)
from convert.adapters.solidworks.sketch.Objects import KDistanceTypes


# the supported inline counts must fit at least a tag for each repeated child
def ReadShortCount(Cursor: SketchArchive) -> int:
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(
        Count <= (len(Cursor.BlobValue) - Cursor.Offset) // 2,
        True,
        "bounded sketch group",
    )
    return Count


# unknown geometry groups must remain empty before supported distance classes can allocate
def ReadDims(Cursor: SketchArchive) -> None:
    RequireArch(
        Cursor.ReadInts("<11i"), (0,) * 11, "empty remaining inline geometry groups"
    )
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty sgValG1Dim group")
    for _ in range(ReadShortCount(Cursor)):
        _ = Cursor.ReadObject(*KDistanceTypes)


# one member logical relations must bind their typed segment handle in this sketch
def ReadRelations(Cursor: SketchArchive) -> list[KRelationRow]:
    RequireArch(
        Cursor.ReadInts("<2H"), (0, 0), "empty sgValG3Dim and sgOffsetDim groups"
    )
    Relations: list[KRelationRow] = []
    for _ in range(ReadShortCount(Cursor)):
        Start = Cursor.Offset
        _, _, TypeValue = ReadDimBase(Cursor, None)
        MemberFlags = Cursor.ReadInts("<2H")
        Target = Cursor.ReadObject("sgLineHandle")
        Relations.append((Start, Cursor.Offset, Target, TypeValue, MemberFlags))
    return Relations


# a coincidence can name only two distinct in scope points when it is active
def ReadPointPair(
    Cursor: SketchArchive, PointIds: list[KPointId], Deleted: int
) -> tuple[list[int], list[int], list[KPointId]]:
    Handles = [Cursor.ReadObject("sgPointHandle") for _ in range(2)]
    Indices: list[int] = []
    for Handle in Handles:
        Index, Owner, Flags = Cursor.Handles[Handle]
        RequireArch((Owner, Flags), (-1, 0), "local coincidence handle")
        Indices.append(Index)
    RequireArch(Cursor.ReadInts("<2H"), (0, 0), "guarded two-point relation flags")
    if Deleted:
        return Handles, Indices, []
    RequireArch(
        len(set(Indices)) == 2 and all(0 <= Index < len(PointIds) for Index in Indices),
        True,
        "distinct local coincidence points",
    )
    return Handles, Indices, [PointIds[Index] for Index in Indices]


# relation state and operands must remain available to the enclosing profile
def ReadCoincidence(Cursor: SketchArchive, PointIds: list[KPointId]) -> Coincidence:
    Start = Cursor.Offset - 2
    DimensionId, _, Suppressed = ReadDimFields(Cursor, None)
    TypeValue, Operands, Deleted, Reserved = Cursor.ReadInts("<i3H")
    RequireArch(
        (DimensionId, TypeValue, Operands, Reserved),
        (-1, 9, 2, 0),
        "two-point coincidence",
    )
    RequireArch(
        (Suppressed, Deleted) in ((0, 0), (1, 0), (0, 1)),
        True,
        "witnessed coincidence state",
    )
    RequireArch(Cursor.ReadInts("<2H"), (65534, 0), "witnessed logical relation flags")
    Handles, Indices, Participants = ReadPointPair(Cursor, PointIds, Deleted)
    return {
        "offset": Start,
        "end": Cursor.Offset,
        "type_code": TypeValue,
        "suppressed": bool(Suppressed),
        "deleted": bool(Deleted),
        "point_handle_objects": Handles,
        "point_indices": Indices,
        "point_native_ids": Participants,
    }
