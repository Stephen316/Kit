# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaOffset,
    MetaProperty,
)


# an immutable segment retains the fields discarded by the projection index
@MakeDataClass(frozen=True, slots=True)
class MetaSegment:
    Header: MetaHeader
    Classes: tuple[MetaClass, ...]
    StoredIds: tuple[int, ...]
    Primary: tuple[MetaOffset, ...]
    Continuations: tuple[MetaOffset, ...]
    NextId: int
    Reserved: int
    Properties: tuple[MetaProperty, ...]
