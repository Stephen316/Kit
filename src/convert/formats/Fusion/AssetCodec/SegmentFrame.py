# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan


# graph checks share the exact emitted record positions before zip assembly
@MakeDataClass(frozen=True, slots=True)
class SegmentFrame:
    Segment: SegmentKind
    BulkData: bytes
    MetaData: bytes
    Spans: tuple[RecordSpan, ...]
    Owners: dict[int, RecordSpan]
