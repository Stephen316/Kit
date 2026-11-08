# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections import Counter

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.RouteEvidence import (
    RouteEvidence,
)
from convert.formats.Fusion.SourceProof.LedgerInput import (
    IndexMembers,
    IndexSpans,
    KDesignStreams,
)
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)
from convert.formats.Fusion.SourceProof.SourceCoverage import (
    CoverageCounts,
    SourceCoverage,
)

# only complete verified dispositions clear entries from the unresolved census
KFullProofs = frozenset(
    (ProofCategory.KVerifiedDesign, ProofCategory.KVerifiedAuxiliary)
)


# observed references do not count as verified coverage for either source layer
def CountProofs(
    Targets: tuple[ArchiveMember | RecordSpan, ...],
    Claims: dict[ArchiveMember | RecordSpan, ProofClaim],
) -> CoverageCounts:
    Counts = Counter(
        Value.Category if (Value := Claims.get(Target)) is not None else None
        for Target in Targets
    )
    return CoverageCounts(
        Counts[None],
        Counts[ProofCategory.KStructural],
        Counts[ProofCategory.KObserved],
        Counts[ProofCategory.KVerifiedDesign],
        Counts[ProofCategory.KVerifiedAuxiliary],
    )


# exact source metadata prevents an identity alone from claiming a different record extent
def MatchClaims(
    Scope: ProofScope,
    MemberIndex: dict[str, ArchiveMember],
    SpanIndex: dict[int, RecordSpan],
    Claims: tuple[ProofClaim, ...],
) -> dict[ArchiveMember | RecordSpan, ProofClaim]:
    Result: dict[ArchiveMember | RecordSpan, ProofClaim] = {}
    for Claim in Claims:
        Target = Claim.Target
        if isinstance(Target, ArchiveMember):
            Found = MemberIndex.get(Target.Name)
            IsDesign = Target.Name in KDesignStreams
        else:
            Found = SpanIndex.get(Target.StartOffset)
            IsDesign = Target.ObjectId in (Scope.HistoryId, Scope.OwnerId)
        if Claim.Scope != Scope or Target != Found or Target in Result:
            raise ValueError(
                "Fusion source proof claim does not match a unique census entry"
            )
        if IsDesign and Claim.Category is ProofCategory.KVerifiedAuxiliary:
            raise ValueError(
                "Fusion source proof cannot classify a design root as auxiliary"
            )
        Result[Target] = Claim
    return Result


# a deterministic report accounts for every central member and every design record
def BuildLedger(
    Scope: ProofScope,
    Members: tuple[ArchiveMember, ...],
    Spans: tuple[RecordSpan, ...],
    Claims: tuple[ProofClaim, ...] = (),
    *,
    ActiveRoutes: RouteEvidence | None = None,
) -> SourceCoverage:
    MemberIndex = IndexMembers(Members)
    SpanIndex = IndexSpans(
        Spans, MemberIndex[KDesignPrefix + "BulkStream.dat"].Size, Scope
    )
    ClaimIndex = MatchClaims(Scope, MemberIndex, SpanIndex, Claims)
    MemberRows = tuple(MemberIndex[NameValue] for NameValue in sorted(MemberIndex))
    SpanRows = tuple(SpanIndex.values())
    Verified = {
        Target for Target, Claim in ClaimIndex.items() if Claim.Category in KFullProofs
    }
    return SourceCoverage(
        Scope,
        CountProofs(MemberRows, ClaimIndex),
        CountProofs(tuple(Value for Value in SpanRows if Value.IsPrimary), ClaimIndex),
        CountProofs(
            tuple(Value for Value in SpanRows if not Value.IsPrimary), ClaimIndex
        ),
        tuple(Value for Value in MemberRows if Value not in Verified),
        tuple(Value for Value in SpanRows if Value not in Verified),
        tuple(
            ClaimIndex[Value]
            for Value in (*MemberRows, *SpanRows)
            if Value in ClaimIndex
        ),
        ActiveRoutes,
    )
