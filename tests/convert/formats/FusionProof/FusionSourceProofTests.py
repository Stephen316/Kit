# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from zipfile import ZipFile

from pytest import MonkeyPatch as PatchContext

from convert.formats.Fusion import ReadFusionDoc
from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.InspectSource import ReadSourceProof
from convert.formats.Fusion.SourceProof.ProofClaim import ProofCategory
from tests.convert.formats.FusionHistoryTests import HistoryArchive

# canonical configuration member paths distinguish proven empty data from arbitrary files
KConfigRoot = "FusionAssetName[Active]/DesignConfigurationTable.BlobParts/"

# a plain empty object is the exact configuration layout covered by the proof
KEmptyConfig = (
    KConfigRoot + "DesignConfigurationTable.00000000-0000-0000-0000-000000000001.dsgcfg"
)


# test envelopes keep the native history bytes independent of the optional attachments
def ProofArchive(Changes: dict[str, bytes]) -> bytes:
    Target = BytesIO()
    with ZipFile(BytesIO(HistoryArchive())) as Source, ZipFile(Target, "w") as Archive:
        for NameValue in Source.namelist():
            if NameValue not in Changes:
                Archive.writestr(NameValue, Source.read(NameValue))
        for NameValue, Value in Changes.items():
            Archive.writestr(NameValue, Value)
    return Target.getvalue()


# proof only reads bounded known metadata and keeps all opaque member identities visible
def TestProofScope(MonkeyPatch: PatchContext) -> None:
    Unknown = (
        KConfigRoot
        + "DesignConfigurationTable.------------------------------------.dsgcfg"
    )
    Changed = (
        KConfigRoot
        + "DesignConfigurationRule.00000000-0000-0000-0000-000000000002.dsgcfgrule"
    )
    Payload = ProofArchive({KEmptyConfig: b"{}", Changed: b"{}\n", Unknown: b"{}"})
    NativeReader = IndexedArchive.ReadMember
    Calls: list[str] = []

    # the call boundary proves ordinary native reads do not inspect extra attachments
    def TrackMember(Archive: IndexedArchive, NameValue: str, Maximum: int) -> bytes:
        Calls.append(NameValue)
        return NativeReader(Archive, NameValue, Maximum)

    MonkeyPatch.setattr(IndexedArchive, "ReadMember", TrackMember)
    Document = ReadFusionDoc(Payload, HistoryId=104)
    assert not Calls
    Proof = ReadSourceProof(Payload, HistoryId=104)
    assert Calls == [KEmptyConfig]
    assert Proof.Scope.SourceDigest == Document.source.sha256
    assert (Proof.Scope.HistoryId, Proof.Scope.OwnerId) == (104, 100)
    assert Proof.MemberCounts.VerifiedAuxiliary == 1
    assert Proof.PrimaryCounts.VerifiedDesign == 2
    assert {Value.Name for Value in Proof.ResidualMembers} >= {Changed, Unknown}
    assert Proof.MemberCounts.Structural == 2
    assert not Proof.IsComplete


# an ignored record header cannot inherit a complete proof from the rest of the chronology
def TestHistVersion() -> None:
    BulkData, Spans = ReadDesignZip(HistoryArchive())
    (History,) = tuple(
        SpanValue for SpanValue in Spans if SpanValue.ClassGuid == KHistoryGuid
    )
    Edited = bytearray(BulkData)
    Edited[History.PayloadOffset] = 1
    Source = ProofArchive({KDesignPrefix + "BulkStream.dat": bytes(Edited)})
    assert ReadFusionDoc(Source).metadata["fusion.history_entries"] == (103, 102, 101)
    Report = ReadSourceProof(Source)
    assert History in Report.ResidualSpans
    assert Report.PrimaryCounts.VerifiedDesign == 1
    assert any(
        Value.Category is ProofCategory.KVerifiedDesign
        and isinstance(Value.Target, RecordSpan)
        and Value.Target.ObjectId == 103
        for Value in Report.Claims
    )
