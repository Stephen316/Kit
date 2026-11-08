# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion import ReadFusionDoc
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.formats.Fusion.FormulaDeps.ParamCollection import KParamCollection
from convert.formats.Fusion.NumericParam import KParamGuid
from convert.formats.Fusion.ParamBinding import KBindingWidths
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.InspectSource import ReadFusionSourceProof
from convert.formats.Fusion.SourceProof.ProofClaim import ProofCategory
from convert.formats.Fusion.SourceProof.SourceCoverage import SourceCoverage
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# equal saved values allow cycles that cannot be rejected by comparing caches alone
KLiteralSource = KStudyPath / "parameteridentity-8fc83529b236" / "01_literal.f3d"


# replacing the design stream pair leaves all indexed positions independently reproducible
def WithBulk(Source: FilePath, BulkData: bytes) -> bytes:
    Buffer = BytesIO()
    with ZipFile(Source) as Before, ZipFile(Buffer, "w") as After:
        After.writestr(KDesignPrefix + "BulkStream.dat", BulkData)
        Name = KDesignPrefix + "MetaStream.dat"
        After.writestr(Name, Before.read(Name))
    return Buffer.getvalue()


# exact native identities expose which records were settled instead of relying on counters
def VerifiedIds(Report: SourceCoverage, Guids: frozenset[str]) -> set[int]:
    return {
        Claim.Target.ObjectId
        for Claim in Report.Claims
        if isinstance(Claim.Target, RecordSpan)
        and Claim.Target.ClassGuid in Guids
        and Claim.Category is ProofCategory.KVerifiedDesign
    }


# a bound formula and all three saved axis factors must receive independent owner proof
@KRequiresCodec
def TestNumericCoverage() -> None:
    Extrude = ReadFusionSourceProof(
        KStudyPath / "holdouts-f8c508a73323" / "expression_depth.f3d"
    )
    Scale = ReadFusionSourceProof(
        KStudyPath / "bodymodes-df9b7113539f" / "scale_nonuniform.f3d"
    )
    assert VerifiedIds(Extrude, frozenset({KParamGuid})) == {202, 276, 279}
    assert len(VerifiedIds(Extrude, frozenset(KBindingWidths))) == 2
    assert VerifiedIds(Scale, frozenset({KParamGuid})) == {251, 254, 283, 286, 289}
    assert len(VerifiedIds(Scale, frozenset(KBindingWidths))) == 5
    assert Scale.MemberCounts.Structural == 5 and not Scale.IsComplete


# a coherent cycle and its downstream formula cannot inherit proof from equal caches
@KRequiresCodec
def TestNumericCycle() -> None:
    BulkData, Spans = ReadDesignZip(KLiteralSource.read_bytes())
    Edited = bytearray(BulkData)
    Params = {
        Span.ObjectId: Span
        for Span in Spans
        if Span.ClassGuid == KParamGuid and Span.IsPrimary
    }
    Literal = "10 mm".encode("utf-16le")
    for Identity, Reference in ((202, "bravo"), (203, "alpha"), (204, "alpha")):
        Span = Params[Identity]
        Start = Edited.index(Literal, Span.PayloadOffset, Span.EndOffset)
        Edited[Start : Start + len(Literal)] = Reference.encode("utf-16le")
    Mutated = WithBulk(KLiteralSource, bytes(Edited))
    Document = ReadFusionDoc(Mutated)
    assert len(Document.parameters) == 3
    Proof = ReadFusionSourceProof(Mutated)
    assert not VerifiedIds(Proof, frozenset({KParamGuid}))
    assert VerifiedIds(Proof, frozenset({KParamCollection}))


# the repeated collection count is required for proof even when permissive parsing can proceed
@KRequiresCodec
def TestNumericCount() -> None:
    BulkData, Spans = ReadDesignZip(KLiteralSource.read_bytes())
    (Collection,) = tuple(
        Span for Span in Spans if Span.ClassGuid == KParamCollection and Span.IsPrimary
    )
    Edited = bytearray(BulkData)
    Edited[Collection.PayloadOffset + 4 + 11] ^= 1
    Mutated = WithBulk(KLiteralSource, bytes(Edited))
    assert len(ReadFusionDoc(Mutated).parameters) == 3
    Proof = ReadFusionSourceProof(Mutated)
    assert not VerifiedIds(Proof, frozenset({KParamGuid, KParamCollection}))
