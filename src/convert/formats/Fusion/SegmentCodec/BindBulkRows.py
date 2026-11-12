from typing import cast as CastValue
from collections.abc import Iterable, Iterator

from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMinClassCode
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.ClassLineage import MapLineage
from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaClasses,
    KMaxMetaIds,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# both streams must agree on classes and ancestry before payloads can be emitted
def BindBulkRows(
    Classes: tuple[MetaClass, ...], Records: Iterable[BulkRecord]
) -> Iterator[BulkRecord]:
    if type(Classes) is not tuple or len(Classes) > KMaxMetaClasses:
        raise ValueError("Invalid Fusion segment class registry")
    Registry = dict(enumerate(Classes, KMinClassCode))
    Parents: dict[str, str] = {}
    Owners: dict[int, int] = {}
    for CodeValue, Entry in Registry.items():
        if (
            not isinstance(CastValue(object, Entry), MetaClass)
            or type(Entry.ClassGuid) is not str
            or type(Entry.BaseGuid) is not str
            or not Entry.ClassGuid
            or Entry.ClassGuid in Parents
            or type(Entry.OwnerIds) is not tuple
            or len(Owners) + len(Entry.OwnerIds) > KMaxMetaIds
        ):
            raise ValueError("Invalid Fusion segment class declaration")
        Parents[Entry.ClassGuid] = Entry.BaseGuid
        for Identity in Entry.OwnerIds:
            if type(Identity) is not int or Identity in Owners:
                raise ValueError("Invalid Fusion segment primary identity")
            Owners[Identity] = CodeValue
    Ranges = MapLineage(Parents)
    for RecordValue in Records:
        if (
            not isinstance(CastValue(object, RecordValue), BulkRecord)
            or type(RecordValue.TypeCode) is not int
            or type(RecordValue.ObjectId) is not int
            or type(RecordValue.IsPrimary) is not bool
        ):
            raise ValueError("Invalid Fusion segment record")
        OwnerCode = Owners.get(RecordValue.ObjectId)
        ClassValue = Registry.get(RecordValue.TypeCode)
        if (
            OwnerCode is None
            or ClassValue is None
            or (RecordValue.IsPrimary and RecordValue.TypeCode != OwnerCode)
        ):
            raise ValueError("Fusion segment record disagrees with class registry")
        if not RecordValue.IsPrimary:
            OwnerStart = Ranges[Registry[OwnerCode].ClassGuid][0]
            ClassStart, ClassEnd = Ranges[ClassValue.ClassGuid]
            if not ClassStart < OwnerStart < ClassEnd:
                raise ValueError("Fusion segment record disagrees with class registry")
        yield RecordValue
