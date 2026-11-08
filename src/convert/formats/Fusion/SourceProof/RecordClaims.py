# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.HistoryGroup import KGroupGuid
from convert.formats.Fusion.NativeHistory import KHistoryGuid, ReadHistory
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentProvenance import IterProvenance


# selected chronology is complete only for the version with fully consumed history payloads
def ReadChronologyClaims(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Scope: ProofScope,
) -> tuple[ProofClaim, ...]:
    Owners = {Span.ObjectId: Span for Span in Spans if Span.IsPrimary}
    History = Owners[Scope.HistoryId]
    if History.ClassGuid != KHistoryGuid:
        raise ValueError("Fusion source proof history identity changed")
    OwnerId, Entries, Groups = ReadHistory(BulkData, History, Owners)
    Expected = tuple(
        (Group["id"], Group["name"], Group["collapsed"], Group["members"])
        for Group in Document.metadata["fusion.history_groups"]
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
    return tuple(
        ProofClaim(
            Scope, Span, ProofCategory.KVerifiedDesign, "exact history chronology"
        )
        for Span in Candidates
        if Span.ClassGuid in {KHistoryGuid, KGroupGuid}
        and BulkData[Span.PayloadOffset : Span.PayloadOffset + 4] == bytes(4)
    )


# neutral provenance can identify a record without establishing all of its semantics
def ReadRecordClaims(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Scope: ProofScope,
) -> tuple[ProofClaim, ...]:
    Verified = ReadChronologyClaims(Document, BulkData, Spans, Scope)
    Complete = {Claim.Target for Claim in Verified}
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
    return Verified + tuple(
        ProofClaim(Scope, Span, ProofCategory.KObserved, "neutral source provenance")
        for Span in Spans
        if Span not in Complete
        and (Span.StartOffset, Span.EndOffset - Span.StartOffset, Span.ClassGuid)
        in Observed
    )
