from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# the version decision must stay consistent so entity identifiers retain their schema and reference meaning
def HasVersion(Entry: MetaClass, Catalog: NativeCatalog) -> bool:
    return any(
        Schema.SchemaVersion == Entry.SchemaVersion
        for Schema in Catalog.Classes.get(Entry.ClassGuid.upper(), ())
    )


# opaque schema needs an explicit validity boundary so entity identifiers retain their schema and reference meaning
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
