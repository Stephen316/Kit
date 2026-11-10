# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# metadata class registration separates history groups from feature entries
KGroupGuid = "A917FE80-93D6-45AD-B741-93BB1ACA5E61"


# group identity and collapse state preserve the original history structure
@Dataclass(frozen=True, slots=True)
class HistoryGroup:
    ObjectId: int
    GroupName: str
    IsCollapsed: bool
    MemberIds: tuple[int, ...]


# a group must name its members explicitly before projecting its timeline
def ReadGroup(BodyValue: bytes, ObjectId: int) -> HistoryGroup:
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(6) != b"\0\0\1\0\0\0":
        raise ValueError("Invalid Fusion history group prefix")
    State = Cursor.TakeBytes(1)
    Count = Cursor.ReadCount(100000)
    if State not in (b"\0", b"\1") or Count == 0 or 17 + 11 * Count > len(BodyValue):
        raise ValueError("Invalid Fusion history group framing")
    Members = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Invalid Fusion history group name separator")
    NameValue = Cursor.ReadText(True, Maximum=1024)
    if Cursor.Offset != len(BodyValue) or len(set(Members)) != Count:
        raise ValueError("Invalid Fusion history group members or suffix")
    return HistoryGroup(ObjectId, NameValue, State == b"\0", Members)
