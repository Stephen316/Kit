# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections import Counter

from convert.formats.Fusion.Assembly.ComponentRead import KComponentBase

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.Edits.Copy.CopyOccurrence import (
    KCopyOccurrence,
    ReadEditCopy,
)
from convert.formats.Fusion.Assembly.Edits.EditSnapshot import (
    KEditSnapshot,
    ReadEditSnap,
)
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.document.models.DocumentModel import AssemblyData
from interchange.features.FeatureStep import FeatureStep


# only active typed placement edits with a reciprocal graph occurrence can be skipped
def ReadAsmEdits(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Assembly: AssemblyData,
    Steps: tuple[FeatureStep, ...],
) -> dict[str, int]:
    Owners: dict[int, RecordSpan] = {}
    ComponentSpans: dict[int, RecordSpan] = {}
    for SpanValue in Spans:
        if SpanValue.IsPrimary:
            Records = Owners
        elif SpanValue.ClassGuid == KComponentBase:
            Records = ComponentSpans
        else:
            continue
        if (
            SpanValue.ObjectId in Records
            or not 0 <= SpanValue.StartOffset <= SpanValue.PayloadOffset
            or not SpanValue.PayloadOffset <= SpanValue.EndOffset <= len(BulkData)
        ):
            return {}
        Records[SpanValue.ObjectId] = SpanValue
    Definitions = {
        Value.id: int(Value.provenance.native_id)
        for Value in Assembly.definitions
        if Value.provenance is not None
    }
    Occurrences = {
        int(Value.provenance.native_id): Value
        for Value in Assembly.instances
        if Value.provenance is not None
    }
    if (
        len(Definitions) != len(Assembly.definitions)
        or len(set(Definitions.values())) != len(Definitions)
        or len(Occurrences) != len(Assembly.instances)
    ):
        return {}
    IndexValue = AsmEditIndex(Owners, ComponentSpans, Definitions, Occurrences)
    return ReadAsmTimeline(BulkData, IndexValue, Steps)


# only ordered edit steps with unique proven occurrences qualify as replayed assembly changes
def ReadAsmTimeline(
    BulkData: bytes, IndexValue: AsmEditIndex, Steps: tuple[FeatureStep, ...]
) -> dict[str, int]:
    StepIds = {
        int(StepValue.provenance.native_id): StepValue.id
        for StepValue in Steps
        if StepValue.provenance is not None
    }
    if (
        len(StepIds) != len(Steps)
        or len(set(StepIds.values())) != len(Steps)
        or any(First.order >= Second.order for First, Second in zip(Steps, Steps[1:]))
    ):
        return {}
    TimelineIds = frozenset(StepIds)
    Snapshots: dict[int, int] = {}
    Verified: dict[str, int] = {}
    for Identity, StepId in StepIds.items():
        EditSpan = IndexValue.Owners.get(Identity)
        if EditSpan is None:
            continue
        try:
            if EditSpan.ClassGuid == KEditSnapshot:
                OccurrenceId = ReadEditSnap(BulkData, IndexValue, Identity, TimelineIds)
                Snapshots[Identity] = OccurrenceId
                Verified[StepId] = OccurrenceId
            elif EditSpan.ClassGuid == KCopyOccurrence:
                Verified[StepId] = ReadEditCopy(
                    BulkData, IndexValue, Identity, Snapshots
                )
        except ValueError:
            continue
    Counts = Counter(Verified.values())
    return {
        StepId: Identity
        for StepId, Identity in Verified.items()
        if Counts[Identity] == 1
    }
