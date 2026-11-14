from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog
from convert.formats.Fusion.EntityCodec.Vocabulary.OpaqueSchema import (
    HasVersion,
    OpaqueSchema,
)
from convert.formats.Fusion.EntityCodec.Vocabulary.PickSchema import PickSchema
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def SelectClasses(
    Classes: tuple[MetaClass, ...], Catalog: NativeCatalog, Opaque: bool = False
) -> dict[str, ClassSchema]:
    if not 1 <= len(Classes) <= KMaxCount:
        raise ValueError("Unqualified Fusion native metadata class count")
    Selected: dict[str, ClassSchema] = {}
    for Entry in Classes:
        if type(Entry.SchemaVersion) is not int:
            raise ValueError("Unqualified Fusion native schema version")
        Schema = (
            PickSchema(Entry.ClassGuid, Entry.SchemaVersion, Catalog)
            if not Opaque or HasVersion(Entry, Catalog)
            else OpaqueSchema(Entry)
        )
        Identity = Entry.ClassGuid.upper()
        if Identity in Selected or Schema.BaseGuid.upper() != Entry.BaseGuid.upper():
            raise ValueError("Unqualified Fusion native duplicate class or base")
        Selected[Identity] = Schema
    return Selected
