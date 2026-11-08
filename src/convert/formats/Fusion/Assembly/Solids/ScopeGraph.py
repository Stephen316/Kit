# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter

from convert.formats.Fusion.Assembly.AssemblyHistory import KContainerGuid, HistoryLink
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# paired history edges distinguish actual feature scope from profile ownership
KDependencyGraph = "B13113CC-031E-4F93-8240-C4C10728869F"


# forward and inverse tables preserve exact typed edges before interpreting flags
def ReadScopeEdges(
    Cursor: MetaCursor, Owners: dict[int, RecordSpan], Reverse: bool
) -> Counter[tuple[int, int, int]]:
    Edges: Counter[tuple[int, int, int]] = Counter()
    Seen: set[int] = set()
    Remaining = 100000
    for Index in range(Cursor.ReadCount(100000)):
        Source = ReadNativeRef(Cursor)
        if Source not in Owners or Source in Seen:
            raise ValueError("Fusion dependency graph source is missing or repeated")
        Seen.add(Source)
        Count = Cursor.ReadCount(Remaining)
        Remaining -= Count
        for EdgeIndex in range(Count):
            Target = ReadNativeRef(Cursor)
            Flags = Cursor.ReadWord()
            if Target not in Owners:
                raise ValueError("Fusion dependency graph target is missing")
            Edge = (Target, Source, Flags) if Reverse else (Source, Target, Flags)
            Edges[Edge] += 1
    return Edges


# only the reciprocal graph referenced by the selected history can bind its scopes
def ReadScopeGraph(
    BulkData: bytes, Owners: dict[int, RecordSpan], OwnerId: int
) -> Counter[tuple[int, int, int]]:
    SelectCursor(BulkData, Owners, OwnerId, KContainerGuid)
    GraphId = HistoryLink(BulkData, Owners[OwnerId], 44)
    Cursor = SelectCursor(BulkData, Owners, GraphId, KDependencyGraph)
    if Cursor.TakeBytes(3) != b"\0\0\1":
        raise ValueError("Unsupported Fusion active dependency graph prefix")
    Forward = ReadScopeEdges(Cursor, Owners, False)
    if (
        ReadNativeRef(Cursor) != OwnerId
        or ReadScopeEdges(Cursor, Owners, True) != Forward
        or Cursor.Offset != len(Cursor.DataValue)
    ):
        raise ValueError("Fusion dependency graph owner or reciprocal edges disagree")
    return Forward
