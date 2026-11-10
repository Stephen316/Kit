# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.OccurAttributes import ReadOccurAttrs
from convert.formats.Fusion.Assembly.OccurRecord import OccurRecord
from convert.formats.Fusion.Assembly.OccurTransform import ReadOccurMatrix
from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# occurrence records store the complete name and placement before the parent link
KOccurrenceGuid = "CE2913AA-CFE0-4F04-9102-24424ED3BCFA"


# verify repeated component references before interpreting an occurrence transform
def ReadOccurrence(DataValue: bytes, ObjectId: int) -> OccurRecord:
    Cursor = MetaCursor(DataValue)
    NameValue = Cursor.ReadText(Maximum=1024)
    if Cursor.TakeBytes(5) != b"\1\1\0\0\0":
        raise ValueError("Unsupported Fusion occurrence prefix")
    ComponentId = ReadNativeRef(Cursor)
    ReadOccurAttrs(Cursor, NameValue)
    _ = Cursor.TakeBytes(2)
    Instance = Cursor.ReadWord()
    _ = ReadSelectUuid(Cursor)
    NativeGuid = ReadSelectUuid(Cursor)
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion occurrence identity marker")
    _ = Cursor.ReadLong()
    if Cursor.TakeBytes(7) != b"\0\1\1\0\0\0\0" or ReadNativeRef(Cursor) != ComponentId:
        raise ValueError("Fusion occurrence component references disagree")
    Matrix = ReadOccurMatrix(Cursor)
    if Cursor.TakeBytes(9) != bytes(9):
        raise ValueError("Unsupported Fusion occurrence transform suffix")
    CollectionId = ReadOptRefMut(Cursor)
    if (
        Cursor.Offset != len(DataValue)
        or ((CollectionId is None) != (NameValue == "rootInstance" and Instance == 0))
        or (CollectionId is not None and (NameValue == "rootInstance" or not Instance))
    ):
        raise ValueError("Invalid Fusion occurrence root or child identity")
    return OccurRecord(
        ObjectId, ComponentId, CollectionId, NameValue, Instance, NativeGuid, Matrix
    )
