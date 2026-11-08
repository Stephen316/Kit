# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaClasses,
    KMaxMetaIds,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass, MetaOffset


# registry ownership remains attached to its declaration until bulk indexing
def ReadWireClasses(Cursor: MetaCursor) -> tuple[MetaClass, ...]:
    RowsValue: list[MetaClass] = []
    Remaining = KMaxMetaIds
    for Index in range(Cursor.ReadCount(KMaxMetaClasses)):
        ClassGuid, BaseGuid = Cursor.ReadText(), Cursor.ReadText()
        Flags, ClassSpace = Cursor.ReadWord(), Cursor.ReadText()
        Count = Cursor.ReadCount(Remaining)
        OwnerIds = tuple(Cursor.ReadLong() for OwnerIndex in range(Count))
        RowsValue.append(MetaClass(ClassGuid, BaseGuid, Flags, ClassSpace, OwnerIds))
        Remaining -= Count
    return tuple(RowsValue)


# an ordered offset table can be reconstructed without imposing physical record order
def ReadWireTable(Cursor: MetaCursor) -> tuple[MetaOffset, ...]:
    return tuple(
        MetaOffset(Cursor.ReadLong(), Cursor.ReadLong())
        for Index in range(Cursor.ReadCount(KMaxMetaIds))
    )
