from types import MappingProxyType as ReadOnlyMap

from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog


# the document catalog contract needs a shared interpretation so model state retains its native feature and ownership relationships
def DocumentCatalog(Schemas: tuple[ClassSchema, ...]) -> NativeCatalog:
    Native = ReadCatalog()
    Classes = dict(Native.Classes)
    for Schema in Schemas:
        Identity = Schema.ClassGuid.upper()
        Versions = Classes.get(Identity, ())
        if not any(Value.SchemaVersion == Schema.SchemaVersion for Value in Versions):
            Classes[Identity] = (*Versions, Schema)
    return NativeCatalog(ReadOnlyMap(Classes), Native.NamedTypes)
