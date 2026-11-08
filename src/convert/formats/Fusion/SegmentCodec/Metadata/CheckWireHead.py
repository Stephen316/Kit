# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.MetaIndex import KSegmentLayout, SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader


# both directions qualify the same version and segment layout before handling records
def CheckWireHead(Header: MetaHeader) -> None:
    if not isinstance(Header, MetaHeader) or not isinstance(
        Header.Segment, SegmentKind
    ):
        raise ValueError("Unsupported Fusion MetaStream segment kind")
    ExpectedId, ExpectedStorage = KSegmentLayout[Header.Segment]
    if (
        Header.Magic != 1234
        or Header.Version != 8
        or Header.RepeatedKind != Header.Segment.value
        or type(Header.HeaderWords) is not tuple
        or len(Header.HeaderWords) != 2
        or type(Header.StorageWords) is not tuple
        or Header.StorageWords != ExpectedStorage
        or (ExpectedId is not None and Header.SegmentId != ExpectedId)
    ):
        raise ValueError("Unsupported Fusion MetaStream header")
