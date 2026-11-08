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
from convert.formats.Fusion.SelectionRef import ReadEntityLeaf, ReadSelectUuid

# root context identity is separately recorded beside the selected body anchor
KBodyContext = "C46D3EEB-40E1-43FA-83DC-9CB204335417"

# the context backend carries an independent typed terminal entity reference
KBodyCtxBackend = "CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C"


# matching root context proves the same body without interpreting instance transforms
def CheckBodyCtx(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ContextId: int,
    Namespace: str,
    EntityGuid: str,
    ExpectedId: int,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, ContextId, KBodyContext)
    if len(Cursor.DataValue) != 181 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion body pick root context")
    Cursor.ReadLong()
    if (
        ReadSelectUuid(Cursor) != Namespace
        or ReadSelectUuid(Cursor) != EntityGuid
        or Cursor.ReadLong() != 2
    ):
        raise ValueError("Fusion body pick root context namespace disagrees")
    Backend = SelectCursor(BulkData, Owners, ReadNativeRef(Cursor), KBodyCtxBackend)
    if len(Backend.DataValue) != 14 or Backend.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion body pick context backend")
    LeafId = ReadNativeRef(Backend)
    if (
        Backend.TakeBytes(1) != bytes(1)
        or ReadEntityLeaf(BulkData, Owners, LeafId) != ExpectedId
    ):
        raise ValueError("Fusion body pick context selects a different entity")
