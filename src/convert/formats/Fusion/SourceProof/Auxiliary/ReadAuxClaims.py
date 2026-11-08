# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import ReadAuxFrame
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)


# framed auxiliary pairs remain unresolved until their native semantic roles are proven
def ReadAuxClaims(Archive: IndexedArchive, Scope: ProofScope) -> tuple[ProofClaim, ...]:
    Claims: list[ProofClaim] = []
    for Segment in (SegmentKind.KBrowser, SegmentKind.KAct):
        try:
            Frame = ReadAuxFrame(Archive, Segment)
        except ValueError:
            continue
        for Member in (Frame.BulkMember, Frame.MetaMember):
            Claims.append(
                ProofClaim(
                    Scope,
                    Member,
                    ProofCategory.KStructural,
                    f"active {Segment.value} index",
                )
            )
    return tuple(Claims)
