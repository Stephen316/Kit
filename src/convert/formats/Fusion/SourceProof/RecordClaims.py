# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectMap, IsObjectTuple
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.HistoryGroup import KGroupGuid
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.NativeHistory import KHistoryGuid, ReadHistory
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Parameters.NumberClaims import ReadParamClaims
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentProvenance import IterProvenance


# selected chronology is complete only for the version with fully consumed history payloads
def ReadOrderClaims(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Scope: ProofScope,
) -> tuple[HistoryPart, tuple[ProofClaim, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    History = Owners[Scope.HistoryId]
    if History.ClassGuid != KHistoryGuid:
        raise ValueError("Fusion source proof history identity changed")
    OwnerId, Entries, Groups = ReadHistory(BulkData, History, Owners)
    SavedGroups = Document.metadata["fusion.history_groups"]
    if not IsObjectTuple(SavedGroups) or not all(
        IsObjectMap(Group) for Group in SavedGroups
    ):
        raise ValueError("Fusion source proof chronology groups are invalid")
    Expected = tuple(
        (Group["id"], Group["name"], Group["collapsed"], Group["members"])
        for Group in CastValue(tuple[Mapping[object, object], ...], SavedGroups)
    )
    if (
        OwnerId != Scope.OwnerId
        or Entries != Document.metadata["fusion.history_entries"]
        or tuple(
            (Group.ObjectId, Group.GroupName, Group.IsCollapsed, Group.MemberIds)
            for Group in Groups
        )
        != Expected
    ):
        raise ValueError("Fusion source proof chronology disagrees with the document")
    Candidates = (History, *(Owners[Group.ObjectId] for Group in Groups))
    Claims = tuple(
        ProofClaim(
            Scope, SpanValue, ProofCategory.KVerifiedDesign, "exact history chronology"
        )
        for SpanValue in Candidates
        if SpanValue.ClassGuid in {KHistoryGuid, KGroupGuid}
        and BulkData[SpanValue.PayloadOffset : SpanValue.PayloadOffset + 4] == bytes(4)
    )
    return (
        HistoryPart(
            Scope.HistoryId, OwnerId, Entries, Groups, Document.feature_timeline
        ),
        Claims,
    )


# neutral provenance can identify a record without establishing all of its semantics
def ReadRecClaims(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Scope: ProofScope,
) -> tuple[ProofClaim, ...]:
    History, Chronology = ReadOrderClaims(Document, BulkData, Spans, Scope)
    Claims = Chronology + ReadParamClaims(Document, BulkData, Spans, History, Scope)
    Claimed = {Claim.Target for Claim in Claims}
    Projected = (
        Document.parameters,
        Document.support_planes,
        Document.sketches,
        Document.selections,
        Document.feature_timeline,
        Document.bodies,
        Document.assembly,
        Document.brep,
    )
    Observed = {
        (Value.offset, Value.length, Value.record_kind)
        for Origin in IterProvenance(Projected)
        if Origin.adapter == "fusion.f3d"
        for Value in Origin.spans
        if Value.stream == KDesignPrefix + "BulkStream.dat"
    }
    return Claims + tuple(
        ProofClaim(
            Scope, SpanValue, ProofCategory.KObserved, "neutral source provenance"
        )
        for SpanValue in Spans
        if SpanValue not in Claimed
        and (
            SpanValue.StartOffset,
            SpanValue.EndOffset - SpanValue.StartOffset,
            SpanValue.ClassGuid,
        )
        in Observed
    )
