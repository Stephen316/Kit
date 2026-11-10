# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.RouteEvidence import (
    RouteEvidence,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ReadAssetRoutes import (
    ReadAssetRoutes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import ReadAuxFrame
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)


# framing remains useful when stronger active asset route evidence cannot be established
def ReadAuxProof(
    Archive: IndexedArchive,
    Scope: ProofScope,
    Design: tuple[bytes, bytes, tuple[RecordSpan, ...]] | None = None,
) -> tuple[tuple[ProofClaim, ...], RouteEvidence | None]:
    Claims: list[ProofClaim] = []
    Routes = None
    for Segment in (SegmentKind.KBrowser, SegmentKind.KAct):
        try:
            Frame = ReadAuxFrame(Archive, Segment)
        except ValueError:
            continue
        if Segment is SegmentKind.KAct and Design is not None:
            try:
                Routes = ReadAssetRoutes(Archive, *Design, Frame)
            except ValueError:
                Routes = None
        for Member in (Frame.BulkMember, Frame.MetaMember):
            if Routes is None or Member != Routes.ActMember:
                Claims.append(
                    ProofClaim(
                        Scope,
                        Member,
                        ProofCategory.KStructural,
                        f"active {Segment.value} index",
                    )
                )
    if Routes is not None:
        Claims.extend(
            ProofClaim(
                Scope, Member, ProofCategory.KObserved, "active asset ACT routing"
            )
            for Member in (
                Routes.Manifest.RootMember,
                Routes.Manifest.ActiveMember,
                Routes.ActMember,
            )
        )
    return tuple(Claims), Routes
