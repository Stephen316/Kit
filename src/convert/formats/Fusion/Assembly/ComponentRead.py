# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.ComponentEntry import ComponentEntry
from convert.formats.Fusion.Assembly.NativeComponent import NativeComponent
from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptionalRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# component labels occur in a registered continuation of the primary component
KComponentBase = "42054630-20A0-40E1-B969-CFE9E742F5C9"

# primary identity distinguishes native definitions from unrelated continuations
KComponentGuid = "E03784ED-5E19-4E14-B9F2-3B07017018CD"


# bounded label fields avoid searching opaque component bytes for plausible names
def ReadComponent(DataValue: bytes, ObjectId: int) -> ComponentEntry:
    Cursor = MetaCursor(DataValue)
    Cursor.Offset = 505
    CollectionId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Invalid Fusion component identity prefix")
    NativeGuid = ReadSelectUuid(Cursor)
    LabelText = Cursor.ReadText(True, Maximum=1024)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Invalid Fusion component label terminator")
    RootOccurrence = ReadOptionalRef(Cursor)
    if Cursor.Offset != len(DataValue):
        raise ValueError("Unexpected Fusion component identity suffix")
    return ComponentEntry(
        NativeComponent(ObjectId, LabelText, NativeGuid),
        CollectionId,
        RootOccurrence,
    )
