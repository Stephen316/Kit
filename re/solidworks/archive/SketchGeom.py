"""Read inline models and native relationship targets from guarded sketch groups."""

import math as Math

from SketchCursor import KDistanceTypes
from SketchRoot import Require


# point and line members share visual and identity fields before their geometry
def ReadMember(Cursor):
    Index, Identity = Cursor.ReadValue("<2i")  # 0x144165b and 0x1441698
    Cursor.ReadValue("<HHBIHhf")  # inline visibility/layout, 0x100ef20 and 0x100f020
    RelationTally, Compact = Cursor.ReadValue("<iH")
    if not Compact:
        Cursor.ReadValue("<3Hhf")  # 0x1441ddf through 0x1441e24
    External = Cursor.ReadObject(None, "sgExtEnt_c")
    Flags, FlagsTwo, _ = Cursor.ReadValue("<2Hi")
    if not Compact:
        Cursor.ReadObject(None)  # moGroup
    Require(Cursor.ReadValue("<B"), (0,), "absent member name")
    Cursor.ReadValue("<d2I")
    return Index, Identity, Flags, FlagsTwo, RelationTally, External


# measured sketch points retain their actual local coordinates
def ReadPointItem(Cursor):
    (Subtype,) = Cursor.ReadValue("<H")
    Require(Subtype in (0, 1), True, "supported sketch point subtype")
    _, Identity, _, _, RelationTally, External = ReadMember(Cursor)
    if External:
        Cursor.PointReferences[Identity] = Cursor.SketchReferences[External]
    (Flags,) = Cursor.ReadValue("<H")
    Require(bool(Flags & 0x10), True, "2D sketch point")
    Coords = Cursor.ReadPoint(2)
    Cursor.ReadValue("<2H")
    if not Flags & 0x20:
        Cursor.ReadObject(None, "sgLineHandle")
        Cursor.ReadObject(None, "sgLineHandle")
    Cursor.ReadValue("<H")
    if not Flags & 0x20:
        Cursor.ReadValue("<i")
        Cursor.ReadPoint(2)
        Cursor.ReadPoint(2)
    Require(Cursor.ReadValue("<H"), (0,), "absent point jet")
    Cursor.ReadValue("<H")
    return Identity, RelationTally, Coords


# line connectivity must use serialized point identities within the same sketch
def ReadLineItem(Cursor, PointCount):
    (ModeValue,) = Cursor.ReadValue("<H")
    Require(ModeValue, 0, "supported inline line mode")
    Index, Identity, Flags, FlagsTwo, _, _ = ReadMember(Cursor)
    (FirstPoint,) = Cursor.ReadValue("<H")
    if FirstPoint == 0xFFFF:
        (FirstPoint,) = Cursor.ReadValue("<i")
    (SecondPoint,) = Cursor.ReadValue("<H")
    if SecondPoint == 0xFFFF:
        (SecondPoint,) = Cursor.ReadValue("<i")
    Cursor.ReadValue("<2H")
    (Width,) = Cursor.ReadValue("<d")
    Require(Math.isfinite(Width), True, "finite inline line width")
    if FlagsTwo & 0x200:
        Cursor.ReadPoint(3)
    Cursor.ReadValue("<H")
    Require(
        all(0 <= Endpoint < PointCount for Endpoint in (FirstPoint, SecondPoint)),
        True,
        "valid inline line point indices",
    )
    return Index, Identity, Flags, FirstPoint, SecondPoint


# only exercised value dimension classes have an independently observed layout
def ReadDims(Cursor):
    # Each active modern group before the generic dimension reader takes a dword count.
    Require(
        Cursor.ReadValue("<11i"), (0,) * 11, "empty remaining inline geometry groups"
    )
    Require(Cursor.ReadValue("<H"), (0,), "empty sgValG1Dim group")
    (Count,) = Cursor.ReadValue("<H")
    Require(
        Count <= (len(Cursor.BlobValue) - Cursor.Offset) // 2,
        True,
        "valid sgValG2Dim count",
    )
    for _ in range(Count):
        Cursor.ReadObject(*KDistanceTypes)


# logical members retain typed targets before projecting any relation semantics
def ReadRelations(Cursor):
    Require(Cursor.ReadValue("<2H"), (0, 0), "empty sgValG3Dim and sgOffsetDim groups")
    (Count,) = Cursor.ReadValue("<H")
    Require(
        Count <= (len(Cursor.BlobValue) - Cursor.Offset) // 2,
        True,
        "valid sgLogG1Dim count",
    )
    Relations = []
    for _ in range(Count):
        Start = Cursor.Offset
        _, _, TypeValue = Cursor.ReadDimBase(None)
        MemberFlags = Cursor.ReadValue("<2H")
        Target = Cursor.ReadObject("sgLineHandle")
        Relations.append((Start, Cursor.Offset, Target, TypeValue, MemberFlags))
    return Relations


# the second logical group represents the saved two-point coincidence and its state
def ReadPointCoincidence(Cursor, PointIds):
    Start = Cursor.Offset
    Require(Cursor.ReadValue("<H"), (1,), "one witnessed two-point relation")
    DimensionId, _, Suppressed = Cursor.ReadDimBaseFields(None)
    TypeValue, Operands, Deleted, Reserved = Cursor.ReadValue("<i3H")
    Require(
        (DimensionId, TypeValue, Operands, Reserved),
        (-1, 9, 2, 0),
        "two-point coincidence",
    )
    Require(
        (Suppressed, Deleted) in ((0, 0), (1, 0), (0, 1)),
        True,
        "witnessed coincidence state",
    )
    Require(Cursor.ReadValue("<2H"), (65534, 0), "witnessed logical relation flags")
    Handles = [Cursor.ReadObject("sgPointHandle") for _ in range(2)]
    Indices = []
    for Handle in Handles:
        Index, Owner, Flags = Cursor.Handles[Handle]
        Require((Owner, Flags), (-1, 0), "local coincidence handle")
        Indices.append(Index)
    Require(Cursor.ReadValue("<i"), (0,), "guarded two-point relation trailer")
    Participants = []
    if not Deleted:
        Require(
            len(set(Indices)) == 2 and all(Index < len(PointIds) for Index in Indices),
            True,
            "distinct local coincidence points",
        )
        Participants = [PointIds[Index] for Index in Indices]
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
