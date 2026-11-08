# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.LinkActRoutes import (
    LinkActRoutes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ReadActTable import (
    ReadActTable,
)


# a generated archive needs typed active routes without unknown owners or residual bytes
def CheckAssetAct(
    Design: SegmentFrame, ActFrame: SegmentFrame, SnapshotId: str
) -> None:
    Table = ReadActTable(ActFrame.BulkData, ActFrame.Spans)
    if Table.SnapshotId != SnapshotId:
        raise ValueError("Fusion asset ACT snapshot disagrees with manifest")
    Routes = LinkActRoutes(
        Design.BulkData, Design.Owners, ActFrame.BulkData, ActFrame.Owners, Table
    )
    if not all(RouteValue.IsResolved for RouteValue in Routes):
        raise ValueError("Fusion asset ACT routes contain unresolved native data")
