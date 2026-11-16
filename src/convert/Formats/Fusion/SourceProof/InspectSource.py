from collections.abc import Callable
from pathlib import Path as FilePath

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.ArchiveRead.ReadDesignPair import ReadDesignPair
from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.DocumentRead import ProjectFusDoc
from convert.Formats.Fusion.SourceBytes import LoadFusionBytes
from convert.Formats.Fusion.SourceProof.Auxiliary.ReadAuxProof import ReadAuxProof
from convert.Formats.Fusion.SourceProof.MemberClaims import ReadItemClaims
from convert.Formats.Fusion.SourceProof.ProofClaim import ProofScope
from convert.Formats.Fusion.SourceProof.ProofLedger import BuildLedger
from convert.Formats.Fusion.SourceProof.RecordClaims import ReadRecClaims
from convert.Formats.Fusion.SourceProof.SourceCoverage import SourceCoverage


# strict source work needs a reproducible receipt tied to the exact projection and archive
def ReadSourceProof(
    SourceData: str | FilePath | bytes,
    *,
    HistoryId: int | None = None,
    InflateZstd: Callable[[bytes, int], bytes] | None = None,
) -> SourceCoverage:
    DataValue, SourceName = LoadFusionBytes(SourceData)
    with OpenFusionZip(DataValue, InflateZstd) as Archive:
        BulkData, MetaData = ReadDesignPair(Archive.Entries, Archive.ReadEntryMut)
        Spans = ReadBulkSpans(BulkData, MetaData)
        Document = ProjectFusDoc(
            DataValue, SourceName, BulkData, Spans, HistoryId, Archive.ReadBody
        )
        SelectedId = Document.metadata["fusion.history_id"]
        OwnerId = Document.metadata["fusion.history_owner_id"]
        if type(SelectedId) is not int or type(OwnerId) is not int:
            raise ValueError("Fusion source proof has no selected native history")
        Scope = ProofScope(Document.source.sha256, SelectedId, OwnerId)
        Members = ReadItemClaims(Archive, Scope)
        AuxClaims, Routes = ReadAuxProof(Archive, Scope, (BulkData, MetaData, Spans))
        Claims = Members + AuxClaims + ReadRecClaims(Document, BulkData, Spans, Scope)
        return BuildLedger(Scope, Archive.Members, Spans, Claims, ActiveRoutes=Routes)
