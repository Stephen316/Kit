# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaClasses,
    KMaxMetaIds,
    KMaxMetaProps,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaOffset,
    MetaProperty,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


# native registry order determines implicit class codes without an extra numeric field
def EmitWireClasses(SinkValue: MetaSink, Items: tuple[MetaClass, ...]) -> None:
    SinkValue.AddCount(Items, KMaxMetaClasses)
    Remaining = KMaxMetaIds
    for Entry in Items:
        if not isinstance(Entry, MetaClass):
            raise ValueError("Invalid Fusion MetaStream class row")
        SinkValue.AddText(Entry.ClassGuid)
        SinkValue.AddText(Entry.BaseGuid)
        SinkValue.AddWord(Entry.Flags)
        SinkValue.AddText(Entry.ClassSpace)
        SinkValue.AddCount(Entry.OwnerIds, Remaining)
        Remaining -= len(Entry.OwnerIds)
        for Identity in Entry.OwnerIds:
            SinkValue.AddLong(Identity)


# primary and continuation tables share the same native identity offset layout
def EmitWireTable(SinkValue: MetaSink, Items: tuple[MetaOffset, ...]) -> None:
    SinkValue.AddCount(Items, KMaxMetaIds)
    for Entry in Items:
        if not isinstance(Entry, MetaOffset):
            raise ValueError("Invalid Fusion MetaStream offset row")
        SinkValue.AddLong(Entry.ObjectId)
        SinkValue.AddLong(Entry.Offset)


# opaque property values are emitted in the order represented by the wire model
def EmitWireProps(SinkValue: MetaSink, Items: tuple[MetaProperty, ...]) -> None:
    SinkValue.AddCount(Items, KMaxMetaProps)
    for Entry in Items:
        if not isinstance(Entry, MetaProperty):
            raise ValueError("Invalid Fusion MetaStream property row")
        SinkValue.AddText(Entry.PropName)
        SinkValue.AddWord(Entry.Value)
