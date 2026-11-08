# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor

# typed support framing distinguishes an edit footer from an incidental byte pattern
KStateSupport = "B7F34D7B-DAC4-41A5-B67D-D672537C3BFA"

# native footer support rows refer only to registered supporting record classes
KSupportClasses = frozenset(
    (
        "ABA79BE7-D8D2-4C17-B59B-C2035E111F77",
        "4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE",
        "335CC7BD-BBE5-40AA-9E8C-5EC99D427A3A",
        "C6ACC94D-2248-421C-BFC3-885A5026559F",
    )
)


# a complete support table bounds the verified assembly edit state footer
def CheckEditSup(BulkData: bytes, IndexValue: AsmEditIndex, SupportId: int) -> None:
    Owners = IndexValue.Owners
    Cursor = SelectCursor(BulkData, Owners, SupportId, KStateSupport)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion assembly edit support prefix")
    Count = Cursor.ReadCount(100000)
    if len(Cursor.DataValue) != 14 + 19 * Count:
        raise ValueError("Unsupported Fusion assembly edit support extent")
    Previous = 0
    for _ in range(Count):
        SpanValue = Owners.get(ReadNativeRef(Cursor))
        KeyValue = Cursor.ReadLong()
        if (
            SpanValue is None
            or SpanValue.ClassGuid not in KSupportClasses
            or KeyValue <= Previous
        ):
            raise ValueError("Unsupported Fusion assembly edit support entry")
        Previous = KeyValue
    if Cursor.ReadLong() != Previous + 1:
        raise ValueError("Fusion assembly edit support counter disagrees")
