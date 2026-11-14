from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def HasVersion(Entry: MetaClass, Catalog: NativeCatalog) -> bool:
    return any(
        Schema.SchemaVersion == Entry.SchemaVersion
        for Schema in Catalog.Classes.get(Entry.ClassGuid.upper(), ())
    )


def OpaqueSchema(Entry: MetaClass) -> ClassSchema:
    if type(Entry.SchemaVersion) is not int:
        raise ValueError("Unqualified Fusion native schema version")
    return ClassSchema(
        Entry.ClassGuid.upper(),
        Entry.BaseGuid.upper(),
        Entry.SchemaVersion,
        (),
        IsOpaque=True,
    )
