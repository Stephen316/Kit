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
    for _ in range(Cursor.ReadCount(KMaxMetaClasses)):
        ClassGuid, BaseGuid = Cursor.ReadText(), Cursor.ReadText()
        Flags, ClassSpace = Cursor.ReadWord(), Cursor.ReadText()
        Count = Cursor.ReadCount(Remaining)
        OwnerIds = tuple(Cursor.ReadLong() for _ in range(Count))
        RowsValue.append(MetaClass(ClassGuid, BaseGuid, Flags, ClassSpace, OwnerIds))
        Remaining -= Count
    return tuple(RowsValue)


# an ordered offset table can be reconstructed without imposing physical record order
def ReadWireTable(Cursor: MetaCursor) -> tuple[MetaOffset, ...]:
    return tuple(
        MetaOffset(Cursor.ReadLong(), Cursor.ReadLong())
        for _ in range(Cursor.ReadCount(KMaxMetaIds))
    )
