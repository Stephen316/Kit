# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid

# native body collections establish component scope through reciprocal membership
KBodyCollection = "CD57BC48-50EC-47DC-975A-FB6DEA72F4DA"

# the body and profile must agree on one typed component
KBodyComponent = "E03784ED-5E19-4E14-B9F2-3B07017018CD"


# single body histories must agree with the explicit body collection inventory
def ReadSingleBody(
    BulkData: bytes, Owners: dict[int, RecordSpan], BodyId: int, ComponentId: int
) -> int:
    BodyCursor = SelectCursor(BulkData, Owners, BodyId, KBodyGuid)
    BodyCursor.Offset = len(BodyCursor.DataValue) - 11
    CollectionId = ReadNativeRef(BodyCursor)
    Cursor = SelectCursor(BulkData, Owners, CollectionId, KBodyCollection)
    if Cursor.TakeBytes(3) != bytes(3):
        raise ValueError("Unsupported Fusion body collection prefix")
    Cursor.TakeBytes(4)
    if Cursor.ReadWord() != 1 or ReadNativeRef(Cursor) != BodyId:
        raise ValueError("Fusion result is not the sole collected body")
    RepeatAt = len(Cursor.DataValue) - 26
    if RepeatAt < Cursor.Offset:
        raise ValueError("Truncated Fusion body collection membership")
    Cursor.Offset = RepeatAt
    if (
        Cursor.ReadWord() != 1
        or ReadNativeRef(Cursor) != BodyId
        or ReadNativeRef(Cursor) != ComponentId
    ):
        raise ValueError("Fusion body collection ownership disagrees")
    SelectCursor(BulkData, Owners, ComponentId, KBodyComponent)
    return CollectionId
