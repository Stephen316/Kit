# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as Pack, unpack as Unpack

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid

# typed helpers distinguish stored names from arbitrary strings in body properties
KBodyNameHelper = "702b9cd2-537c-429e-8cc4-22beeeb98c37"


# require both typed links and the bounded property trailer before accepting a name
def ReadBodyName(
    BulkData: bytes, Owners: dict[int, RecordSpan], BodyId: int, CollectionId: int
) -> tuple[str, int]:
    BodyCursor = SelectCursor(BulkData, Owners, BodyId, KBodyGuid)
    BodyData = BodyCursor.DataValue
    if BodyCursor.TakeBytes(2) not in (b"\0\0", b"\0\1"):
        raise ValueError("Unsupported Fusion body name record prefix")
    Marker = Pack("<BQH", 1, CollectionId, 0)
    FieldData = BodyData[:-11]
    Cursor = MetaCursor(FieldData)
    Position = FieldData.find(Marker, 2)
    Matches = []
    while Position != -1:
        Cursor.Offset = Position + len(Marker)
        Position = FieldData.find(Marker, Position + 1)
        try:
            if Cursor.TakeBytes(1) != bytes(1):
                continue
            HelperId = ReadNativeRef(Cursor)
            Helper = Owners.get(HelperId)
            if Helper is None or Helper.ClassGuid.lower() != KBodyNameHelper:
                continue
            NameText = Cursor.ReadText(True, Maximum=1024)
            Color = Unpack("<4f", Cursor.TakeBytes(16))
            Flags = Cursor.TakeBytes(2)
            if all(0 <= Value <= 1 for Value in Color) and all(
                FlagValue in (0, 1) for FlagValue in Flags
            ):
                Matches.append((NameText, HelperId))
        except ValueError:
            continue
    if len(Matches) != 1:
        raise ValueError("Fusion stored body name is missing or ambiguous")
    return Matches[0]
