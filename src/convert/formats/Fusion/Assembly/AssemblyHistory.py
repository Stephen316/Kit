# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.AssemblyModel import NativeAssembly
from convert.formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.RecordSpan import RecordSpan

# history containers bridge component definitions to reciprocal history sequences
KContainerGuid = "C3423E04-7E85-4B44-8E31-A5FA9C100052"


# fixed suffix fields must remain within the validated record that owns them
def HistoryLink(BulkData: bytes, Span: RecordSpan, Distance: int) -> int:
    Start = Span.EndOffset - Distance
    if Start < Span.PayloadOffset + 4:
        raise ValueError("Truncated Fusion assembly history link")
    return ReadNativeRef(MetaCursor(BulkData[Start : Start + 11]))


# only a proven root timeline may represent an assembly with empty child histories
def ResolveAssemblyHistories(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Assembly: NativeAssembly,
    Parts: tuple[HistoryPart, ...],
) -> dict[int, HistoryPart]:
    Primary = {Span.ObjectId: Span for Span in Spans if Span.IsPrimary}
    Indexed = {
        Span.ObjectId for Span in Primary.values() if Span.ClassGuid == KHistoryGuid
    }
    ByHistory = {Part.HistoryId: Part for Part in Parts}
    if Indexed != ByHistory.keys():
        raise ValueError("Fusion assembly has unreadable histories")
    HistoryMap: dict[int, HistoryPart] = {}
    MappedIds: set[int] = set()
    for Component in Assembly.Components:
        ComponentSpan = Primary.get(Component.ObjectId)
        if ComponentSpan is None or ComponentSpan.ClassGuid != KComponentGuid:
            raise ValueError("Unknown Fusion assembly component history layout")
        OwnerId = HistoryLink(BulkData, ComponentSpan, 52)
        OwnerSpan = Primary.get(OwnerId)
        if OwnerSpan is None or OwnerSpan.ClassGuid != KContainerGuid:
            raise ValueError("Missing Fusion assembly component history owner")
        HistoryId = HistoryLink(BulkData, OwnerSpan, 55)
        History = ByHistory.get(HistoryId)
        if History is None or History.OwnerId != OwnerId or HistoryId in MappedIds:
            raise ValueError("Fusion assembly component history links disagree")
        if Component.ObjectId != Assembly.RootComponentId and History.EntryIds:
            raise ValueError("Fusion assembly has a separate nonempty child history")
        HistoryMap[Component.ObjectId] = History
        MappedIds.add(HistoryId)
    if MappedIds != Indexed:
        raise ValueError("Fusion assembly has histories outside its component graph")
    return HistoryMap
