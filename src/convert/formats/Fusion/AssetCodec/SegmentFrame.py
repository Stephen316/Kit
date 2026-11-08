# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
