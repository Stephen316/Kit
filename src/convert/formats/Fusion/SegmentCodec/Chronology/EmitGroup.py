# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from struct import pack as PackValue

from convert.formats.Fusion.HistoryGroup import HistoryGroup
from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import (
    IsHistId,
    PackHistRefs,
)


# timeline groups emit their ordered members and encoded name independently of file offsets
def EmitGroup(Group: HistoryGroup) -> bytes:
    if (
        not isinstance(Group, HistoryGroup)
        or not IsHistId(Group.ObjectId)
        or type(Group.IsCollapsed) is not bool
        or type(Group.GroupName) is not str
        or len(Group.GroupName) > 1024
        or not all(Letter.isprintable() for Letter in Group.GroupName)
        or type(Group.MemberIds) is not tuple
        or not Group.MemberIds
    ):
        raise ValueError("Invalid Fusion chronology group")
    NameData = Group.GroupName.encode("utf-16le")
    NameUnits = len(NameData) // 2
    if NameUnits > 1024:
        raise ValueError("Oversized Fusion chronology group name")
    Members = PackHistRefs(Group.MemberIds)
    if Group.ObjectId in Group.MemberIds:
        raise ValueError("Fusion chronology group cannot contain itself")
    return b"".join(
        (
            bytes(4),
            PackValue("<2xB3xB", 1, not Group.IsCollapsed),
            Members,
            bytes(2),
            PackValue("<I", NameUnits),
            NameData,
        )
    )
