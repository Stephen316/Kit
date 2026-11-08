# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Act.CheckActKey import CheckActKey
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxWireId
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActKeys import KMaxActKeys


# table entries need distinct field references and the native lexical key order
def EmitActKeysMut(SinkValue: MetaSink, Routes: tuple[tuple[int, str], ...]) -> None:
    SinkValue.AddCount(Routes, KMaxActKeys)
    if not Routes:
        raise ValueError("Fusion ACT table has no field routes")
    FieldIds: set[int] = set()
    LastKey = ""
    for EntryRow in Routes:
        if type(EntryRow) is not tuple or len(EntryRow) != 2:
            raise ValueError("Invalid Fusion ACT table route")
        FieldsId, KeyValue = EntryRow
        CheckActKey(KeyValue)
        if (
            type(FieldsId) is not int
            or not 0 < FieldsId < KMaxWireId
            or FieldsId in FieldIds
        ):
            raise ValueError("Invalid or duplicate Fusion ACT field identity")
        if KeyValue <= LastKey:
            raise ValueError("Invalid or unordered Fusion ACT route key")
        SinkValue.AddBytes(PackValue("<BQH", 1, FieldsId, 0))
        SinkValue.AddText(KeyValue, WideText=True)
        FieldIds.add(FieldsId)
        LastKey = KeyValue
