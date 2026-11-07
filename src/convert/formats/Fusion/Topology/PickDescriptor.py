# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid
from convert.formats.Fusion.Topology.TopologyPick import TopologyPick

# the registered topology descriptor has a recipe where an entity pick has a leaf
KTopoSelect = "5662F619-2281-4AD9-93DC-1FCFDA1062E7"

# the typed helper supplies a bounded witness to the descriptor trailer layout
KPickHelper = "5FBE538E-139B-46D4-BCAF-CC796D1E1F78"


# the frame with one context and one anchor is shared across feature classes
def ReadTopoPick(
    BulkData: bytes, Owners: dict[int, RecordSpan], Descriptor: int, FeatureId: int
) -> TopologyPick:
    Cursor = SelectCursor(BulkData, Owners, Descriptor, KTopoSelect)
    if len(Cursor.DataValue) != 276 or Cursor.TakeBytes(4) not in (
        bytes(4),
        b"\0\0\0\1",
    ):
        raise ValueError("Unsupported Fusion topology selection descriptor")
    RecipeId = ReadNativeRef(Cursor)
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion topology selection namespace count")
    Namespace = ReadSelectUuid(Cursor)
    EntityGuid = ReadSelectUuid(Cursor)
    if (Cursor.ReadLong(), Cursor.ReadWord()) != (2, 1):
        raise ValueError("Unsupported Fusion topology selection context count")
    ContextId = ReadNativeRef(Cursor)
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion topology selection anchor count")
    AnchorId = ReadNativeRef(Cursor)
    Cursor.TakeBytes(14)
    if Cursor.TakeBytes(4) != b"\1\1\0\0":
        raise ValueError("Unsupported Fusion topology selection trailer")
    Cursor.TakeBytes(8)
    if Cursor.TakeBytes(4) != b"\1\1\0\0":
        raise ValueError("Unsupported Fusion topology selection helper marker")
    HelperId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion topology selection support marker")
    SupportId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != b"\0" or ReadNativeRef(Cursor) != FeatureId:
        raise ValueError("Fusion topology selection owner disagrees")
    Helper = SelectCursor(BulkData, Owners, HelperId, KPickHelper)
    if Helper.DataValue not in (bytes(10), b"\0\1" + bytes(12)):
        raise ValueError("Unsupported Fusion topology selection helper")
    return TopologyPick(
        RecipeId, ContextId, AnchorId, HelperId, SupportId, Namespace, EntityGuid
    )
