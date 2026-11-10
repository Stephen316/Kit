# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Iterable
from dataclasses import replace as Replace
from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.BindBulkRows import BindBulkRows
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkStream import EmitBulkStream
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaOffset
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.WriteMetaWire import WriteMetaWire


# deriving both index tables from physical positions prevents stale metadata after edits
def EmitSegment(
    Metadata: MetaSegment, Records: Iterable[BulkRecord]
) -> tuple[bytes, bytes]:
    if not isinstance(CastValue(object, Metadata), MetaSegment):
        raise ValueError("Expected typed metadata for Fusion segment")
    BulkData, Entries = EmitBulkStream(BindBulkRows(Metadata.Classes, Records))
    Primary: list[MetaOffset] = []
    Continuations: list[MetaOffset] = []
    for Offset, Identity, IsPrimary in Entries:
        Target = Primary if IsPrimary else Continuations
        Target.append(MetaOffset(Identity, Offset))
    MetaData = WriteMetaWire(
        Replace(Metadata, Primary=tuple(Primary), Continuations=tuple(Continuations))
    )
    return BulkData, MetaData
