# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from pytest import raises as Raises

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)
from convert.formats.Fusion.SourceProof.ProofLedger import BuildLedger
from convert.formats.Fusion.SourceProof.SourceCoverage import CoverageCounts

# a synthetic archive contains both essential streams and an unrelated member
KProofMembers = (
    ArchiveMember("Preview.png", 81, 11, 11, 0, 23, 0, False),
    ArchiveMember(KDesignPrefix + "BulkStream.dat", 0, 70, 30, 8, 44, 0, False),
    ArchiveMember(KDesignPrefix + "MetaStream.dat", 39, 80, 35, 8, 48, 0, False),
)

# a continuation shares a native id while retaining independent extent and class identity
KProofSpans = (
    RecordSpan(0, 15, 20, 35, 257, KHistoryGuid, "", True),
    RecordSpan(20, 35, 38, 26, 258, "Component", "", True),
    RecordSpan(38, 53, 55, 42, 259, "Custom", "", True),
    RecordSpan(55, 70, 70, 42, 260, "Base", "", False),
)

# generated source ids leave no dependence on any particular fusion fixture
KProofScope = ProofScope("a" * 64, 35, 26)


# observed and structural evidence must leave exact unresolved identities in the report
def TestProofGaps() -> None:
    Claims = (
        ProofClaim(
            KProofScope, KProofSpans[2], ProofCategory.KObserved, "timeline reference"
        ),
        ProofClaim(
            KProofScope, KProofMembers[1], ProofCategory.KStructural, "record framing"
        ),
        ProofClaim(
            KProofScope, KProofSpans[0], ProofCategory.KVerifiedDesign, "history decode"
        ),
    )
    Report = BuildLedger(KProofScope, KProofMembers, KProofSpans, Claims)
    assert not Report.IsComplete
    assert Report.MemberCounts == CoverageCounts(2, 1, 0, 0, 0)
    assert Report.PrimaryCounts == CoverageCounts(1, 0, 1, 1, 0)
    assert Report.ContinuationCounts == CoverageCounts(1, 0, 0, 0, 0)
    assert Report.MemberCounts.Total == 3
    assert Report.PrimaryCounts.Residual == 2
    assert Report.ResidualMembers == (*KProofMembers[1:], KProofMembers[0])
    assert Report.ResidualSpans == KProofSpans[1:]
    assert Report.Claims == (Claims[1], Claims[2], Claims[0])
    assert Report == BuildLedger(
        KProofScope,
        tuple(reversed(KProofMembers)),
        tuple(reversed(KProofSpans)),
        tuple(reversed(Claims)),
    )


# complete verification must explicitly clear every member and record including continuations
def TestProofClosed() -> None:
    Claims = tuple(
        ProofClaim(KProofScope, Value, ProofCategory.KVerifiedDesign, "full decoder")
        for Value in (*KProofMembers[1:], *KProofSpans)
    ) + (
        ProofClaim(
            KProofScope,
            KProofMembers[0],
            ProofCategory.KVerifiedAuxiliary,
            "independent presentation payload",
        ),
    )
    Full = BuildLedger(KProofScope, KProofMembers, KProofSpans, Claims)
    assert Full.IsComplete
    assert Full.MemberCounts == CoverageCounts(0, 0, 0, 2, 1)
    assert Full.PrimaryCounts == CoverageCounts(0, 0, 0, 3, 0)
    assert Full.ContinuationCounts == CoverageCounts(0, 0, 0, 1, 0)
    assert not BuildLedger(
        KProofScope,
        KProofMembers,
        KProofSpans,
        tuple(Value for Value in Claims if Value.Target != KProofSpans[-1]),
    ).IsComplete


# proof claims bind exact records and members to a single archive and native history
def TestProofClaims() -> None:
    Claim = ProofClaim(
        KProofScope, KProofSpans[0], ProofCategory.KVerifiedDesign, "history decode"
    )
    for Candidates in (
        (Claim, Claim),
        (Replace(Claim, Scope=Replace(KProofScope, SourceDigest="b" * 64)),),
        (Replace(Claim, Scope=Replace(KProofScope, OwnerId=27)),),
        (Replace(Claim, Target=Replace(KProofSpans[0], EndOffset=21)),),
        (Replace(Claim, Target=Replace(KProofMembers[1], Crc=12)),),
        (Replace(Claim, Target=Replace(KProofSpans[3], IsPrimary=True)),),
    ):
        with Raises(ValueError, match="unique census entry"):
            BuildLedger(KProofScope, KProofMembers, KProofSpans, Candidates)
    with Raises(ValueError, match="design root"):
        BuildLedger(
            KProofScope,
            KProofMembers,
            KProofSpans,
            (Replace(Claim, Category=ProofCategory.KVerifiedAuxiliary),),
        )
    with Raises(ValueError, match="proof scope"):
        Replace(KProofScope, SourceDigest="invalid")


# missing archive facts and omitted design records cannot masquerade as a complete census
def TestProofCensus() -> None:
    for Members in (
        KProofMembers[:2],
        (*KProofMembers, KProofMembers[0]),
        (*KProofMembers, Replace(KProofMembers[0], Name="Other")),
        (
            KProofMembers[0],
            Replace(KProofMembers[1], IsDirectory=True),
            KProofMembers[2],
        ),
    ):
        with Raises(ValueError, match="archive census"):
            BuildLedger(KProofScope, Members, KProofSpans)
    for Spans in (
        KProofSpans[:-1],
        (*KProofSpans[:2], KProofSpans[3]),
        (*KProofSpans, KProofSpans[-1]),
        (*KProofSpans[:3], Replace(KProofSpans[-1], ObjectId=43)),
        (Replace(KProofSpans[0], ClassGuid="Other"), *KProofSpans[1:]),
    ):
        with Raises(ValueError, match="record census"):
            BuildLedger(KProofScope, KProofMembers, Spans)
