# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# segment authoring keeps typed payloads separate from derived index positions
@MakeDataClass(frozen=True, slots=True)
class SegmentPlan:
    Metadata: MetaSegment
    Records: tuple[BulkRecord, ...]
