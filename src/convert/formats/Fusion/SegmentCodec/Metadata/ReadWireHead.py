# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.CheckWireHead import CheckWireHead
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader


# header parsing preserves the repeated kind and opaque versioned fields in wire order
def ReadWireHead(Cursor: MetaCursor, Expected: SegmentKind | None) -> MetaHeader:
    Segment = SegmentKind(Cursor.ReadText())
    if Expected is not None and Expected is not Segment:
        raise ValueError("Unexpected Fusion MetaStream segment kind")
    Header = MetaHeader(
        Segment,
        Cursor.ReadWord(),
        Cursor.ReadText(True),
        Cursor.ReadWord(),
        Cursor.ReadWord(),
        (Cursor.ReadWord(), Cursor.ReadWord()),
        Cursor.ReadText(),
        Cursor.ReadText(),
        (Cursor.ReadWord(), Cursor.ReadWord()),
    )
    CheckWireHead(Header)
    return Header
