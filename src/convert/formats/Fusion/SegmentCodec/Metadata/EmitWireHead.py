# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.SegmentCodec.Metadata.CheckWireHead import CheckWireHead
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


# independent construction must emit the same typed header grammar as reading
def EmitWireHead(SinkValue: MetaSink, Header: MetaHeader) -> None:
    CheckWireHead(Header)
    SinkValue.AddText(Header.Segment.value)
    SinkValue.AddWord(Header.SegmentId)
    SinkValue.AddText(Header.Namespace, WideText=True)
    SinkValue.AddWord(Header.Magic)
    SinkValue.AddWord(Header.Version)
    for Number in Header.HeaderWords:
        SinkValue.AddWord(Number)
    SinkValue.AddText(Header.RepeatedKind)
    SinkValue.AddText(Header.StorageSpace)
    for Number in Header.StorageWords:
        SinkValue.AddWord(Number)
