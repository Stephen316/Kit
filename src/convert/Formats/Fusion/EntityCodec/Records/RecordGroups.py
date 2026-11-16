from convert.Formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.Formats.Fusion.EntityCodec.Schema.ClassGroups import ClassGroups
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog


# the record groups contract needs a shared interpretation so entity identifiers retain their schema and reference meaning
def RecordGroups(
    ObjectId: int, TypeCode: int, Scope: RecordScope, Catalog: EntityCatalog
) -> tuple[ClassSchema, ...]:
    Identity = Scope.ClassCodes[TypeCode]
    Stops = Scope.Continuations.get(ObjectId, frozenset()) - {Identity}
    return ClassGroups(Catalog, Identity, Stops)
