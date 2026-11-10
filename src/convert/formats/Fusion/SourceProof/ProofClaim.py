# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from typing import cast as CastValue
from dataclasses import dataclass as MakeDataClass
from enum import StrEnum

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.RecordSpan import RecordSpan

# history keys must stay within their serialized unsigned width
KMaxNativeId = (1 << 64) - 1


# a proof scope distinguishes original source archives and explicitly selected histories
@MakeDataClass(frozen=True, slots=True)
class ProofScope:
    SourceDigest: str
    HistoryId: int
    OwnerId: int

    # canonical identifiers prevent stale claims from matching a different raw archive
    def __post_init__(self) -> None:
        if (
            type(self.SourceDigest) is not str
            or len(self.SourceDigest) != 64
            or any(Value not in "0123456789abcdef" for Value in self.SourceDigest)
            or any(
                type(Value) is not int or not 1 <= Value <= KMaxNativeId
                for Value in (self.HistoryId, self.OwnerId)
            )
        ):
            raise ValueError("Invalid Fusion source proof scope")


# framing and references convey evidence without proving a complete semantic disposition
class ProofCategory(StrEnum):
    KStructural = "structural"
    KObserved = "observed"
    KVerifiedDesign = "verified_design"
    KVerifiedAuxiliary = "verified_auxiliary"


# a claim applies only to one exact native census entry in one proof scope
@MakeDataClass(frozen=True, slots=True)
class ProofClaim:
    Scope: ProofScope
    Target: ArchiveMember | RecordSpan
    Category: ProofCategory
    Evidence: str

    # complete dispositions must be explicit typed claims with a named evidence producer
    def __post_init__(self) -> None:
        if (
            not isinstance(CastValue(object, self.Scope), ProofScope)
            or not isinstance(
                CastValue(object, self.Target), (ArchiveMember, RecordSpan)
            )
            or not isinstance(CastValue(object, self.Category), ProofCategory)
            or type(self.Evidence) is not str
            or len(self.Evidence) > 1024
            or not self.Evidence.strip()
        ):
            raise ValueError("Invalid Fusion source proof claim")
