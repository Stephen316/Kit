# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.ProofClaim import ProofClaim, ProofScope


# count fields keep observations separate from fully verified dispositions
@MakeDataClass(frozen=True, slots=True)
class CoverageCounts:
    Unclaimed: int
    Structural: int
    Observed: int
    VerifiedDesign: int
    VerifiedAuxiliary: int

    # every unknown observed or structurally qualified row still needs a complete proof
    @property
    def Residual(self) -> int:
        return self.Unclaimed + self.Structural + self.Observed

    # census counts include the complete proof outcomes as well as unresolved entries
    @property
    def Total(self) -> int:
        return self.Residual + self.VerifiedDesign + self.VerifiedAuxiliary


# an immutable report retains exact evidence and every entry still needing verification
@MakeDataClass(frozen=True, slots=True)
class SourceCoverage:
    Scope: ProofScope
    MemberCounts: CoverageCounts
    PrimaryCounts: CoverageCounts
    ContinuationCounts: CoverageCounts
    ResidualMembers: tuple[ArchiveMember, ...]
    ResidualSpans: tuple[RecordSpan, ...]
    Claims: tuple[ProofClaim, ...]

    # semantic closure requires complete verification of every indexed source entry
    @property
    def IsComplete(self) -> bool:
        return not self.ResidualMembers and not self.ResidualSpans
