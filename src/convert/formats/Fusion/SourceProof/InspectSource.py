# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from pathlib import Path as FilePath

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionArchive
from convert.formats.Fusion.ArchiveRead.ReadDesignPair import ReadDesignPair
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DocumentRead import ProjectFusionDoc
from convert.formats.Fusion.SourceBytes import LoadFusionBytes
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxProof import ReadAuxProof
from convert.formats.Fusion.SourceProof.MemberClaims import ReadMemberClaims
from convert.formats.Fusion.SourceProof.ProofClaim import ProofScope
from convert.formats.Fusion.SourceProof.ProofLedger import BuildLedger
from convert.formats.Fusion.SourceProof.RecordClaims import ReadRecordClaims
from convert.formats.Fusion.SourceProof.SourceCoverage import SourceCoverage


# strict source work needs a reproducible receipt tied to the exact projection and archive
def ReadFusionSourceProof(
    SourceData: str | FilePath | bytes,
    *,
    HistoryId: int | None = None,
    InflateZstd: Callable[[bytes, int], bytes] | None = None,
) -> SourceCoverage:
    DataValue, SourceName = LoadFusionBytes(SourceData)
    with OpenFusionArchive(DataValue, InflateZstd) as Archive:
        BulkData, MetaData = ReadDesignPair(Archive)
        Spans = ReadBulkSpans(BulkData, MetaData)
        Document = ProjectFusionDoc(
            DataValue, SourceName, BulkData, Spans, HistoryId, Archive.ReadBody
        )
        SelectedId = Document.metadata["fusion.history_id"]
        OwnerId = Document.metadata["fusion.history_owner_id"]
        if type(SelectedId) is not int or type(OwnerId) is not int:
            raise ValueError("Fusion source proof has no selected native history")
        Scope = ProofScope(Document.source.sha256, SelectedId, OwnerId)
        Members = ReadMemberClaims(Archive, Scope)
        AuxClaims, Routes = ReadAuxProof(Archive, Scope, (BulkData, MetaData, Spans))
        Claims = (
            Members + AuxClaims + ReadRecordClaims(Document, BulkData, Spans, Scope)
        )
        return BuildLedger(Scope, Archive.Members, Spans, Claims, ActiveRoutes=Routes)
