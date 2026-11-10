# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.Edits.EditCreation import KNilNamespace
from convert.formats.Fusion.Assembly.OccurTransform import ReadOccurMatrix
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# context frames reference explicit occurrence routes through counted typed wrappers
KCopyFrame = "2E3AC990-483D-4A55-8662-C064B976A957"

# the wrapper bounds the single route expected in each copy context slot
KCopyRouteList = "FF415D89-A1DB-44AC-B824-E9A772B86ED4"

# a populated occurrence route stores the source instance uuid separately from the terminal pair
KCopyRoute = "96CBEA21-17E0-4BCB-BA77-04EA87B47934"


# two frame contexts describe the same target namespace through distinct routes
def ReadCopyFrame(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    FrameId: int,
    OwnerId: int,
    Populated: bool,
) -> tuple[int, tuple[float, ...], str, tuple[str, str]]:
    Owners = IndexValue.Owners
    Cursor = SelectCursor(BulkData, Owners, FrameId, KCopyFrame)
    if (
        Cursor.TakeBytes(20) != bytes(20)
        or Cursor.ReadWord() != 3
        or Cursor.TakeBytes(13) != bytes(13)
    ):
        raise ValueError("Unsupported Fusion copy context frame")
    LinkId = ReadNativeRef(Cursor)
    if (Cursor.DataValue[Cursor.Offset : Cursor.Offset + 1] == b"\0") != Populated:
        raise ValueError("Fusion copy context transform mode disagrees")
    Matrix = ReadOccurMatrix(Cursor)
    if Cursor.TakeBytes(1) != bytes(1) or ReadNativeRef(Cursor) != OwnerId:
        raise ValueError("Fusion copy context owner disagrees")
    WrapperId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(6) != bytes(6) or Cursor.Offset != len(Cursor.DataValue):
        raise ValueError("Unsupported Fusion copy context suffix")
    NativeGuid, Terminal = ReadCopyRoute(BulkData, Owners, WrapperId, Populated)
    return LinkId, Matrix, NativeGuid, Terminal


# route ownership and namespace have their own record framing
def ReadCopyRoute(
    BulkData: bytes, Owners: dict[int, RecordSpan], WrapperId: int, Populated: bool
) -> tuple[str, tuple[str, str]]:
    Wrapper = SelectCursor(BulkData, Owners, WrapperId, KCopyRouteList)
    if (
        len(Wrapper.DataValue) != 18
        or Wrapper.TakeBytes(3) != bytes(3)
        or Wrapper.ReadWord() != 1
    ):
        raise ValueError("Unsupported Fusion copy context route count")
    Route = SelectCursor(BulkData, Owners, ReadNativeRef(Wrapper), KCopyRoute)
    if Route.TakeBytes(2) != bytes(2) or Route.ReadWord() != int(Populated):
        raise ValueError("Unsupported Fusion copy context route mode")
    NativeGuid = ReadSelectUuid(Route)
    Namespace = None
    if Populated:
        Namespace = ReadSelectUuid(Route)
        _ = ReadSelectUuid(Route)
        if NativeGuid == KNilNamespace or Route.ReadLong() != 2:
            raise ValueError("Unsupported Fusion copy populated route")
    elif NativeGuid != KNilNamespace or Route.ReadWord() != 0 or Route.ReadLong() != 1:
        raise ValueError("Unsupported Fusion copy empty route")
    Terminal = ReadSelectUuid(Route), ReadSelectUuid(Route)
    if (
        (Populated and Terminal[0] != Namespace)
        or Route.ReadLong() != 2
        or Route.ReadWord() != 0
        or Route.Offset != len(Route.DataValue)
    ):
        raise ValueError("Fusion copy context route terminal disagrees")
    return NativeGuid, Terminal
