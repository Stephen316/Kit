# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.LinkActRoutes import (
    LinkActRoutes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.RouteEvidence import (
    RouteEvidence,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.RouteMembers import (
    ReadRouteFiles,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ReadActTable import (
    ReadActTable,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    ReadActiveMeta,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import AuxFrame


# one archive session binds both manifest ids and reciprocal records to exact members
def ReadAssetRoutes(
    Archive: IndexedArchive,
    DesignBulk: bytes,
    DesignMeta: bytes,
    DesignSpans: tuple[RecordSpan, ...],
    ActFrame: AuxFrame,
) -> RouteEvidence:
    DesignMember, DesignIndex = ReadRouteFiles(
        Archive, DesignBulk, DesignMeta, ActFrame
    )
    Cursor = MetaCursor(DesignMeta)
    if Cursor.ReadText() != SegmentKind.KDesign or Cursor.ReadWord() != 0:
        raise ValueError("Unsupported Fusion ACT route Design segment")
    Manifest = ReadActiveMeta(Archive)
    Table = ReadActTable(ActFrame.BulkData, ActFrame.Spans)
    if Table.SnapshotId != Manifest.SnapshotId:
        raise ValueError("Fusion ACT route snapshot disagrees with active manifest")
    DesignOwners = {
        EntrySpan.ObjectId: EntrySpan
        for EntrySpan in DesignSpans
        if EntrySpan.IsPrimary
    }
    ActOwners = {
        EntrySpan.ObjectId: EntrySpan
        for EntrySpan in ActFrame.Spans
        if EntrySpan.IsPrimary
    }
    Routes = LinkActRoutes(
        DesignBulk, DesignOwners, ActFrame.BulkData, ActOwners, Table
    )
    return RouteEvidence(
        Manifest,
        DesignMember,
        DesignIndex,
        ActFrame.BulkMember,
        ActFrame.MetaMember,
        Table,
        Routes,
    )
