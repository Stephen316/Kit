from convert.formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.formats.Fusion.EntityCodec.Schema.ClassGroups import ClassGroups
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog


def RecordGroups(
    ObjectId: int, TypeCode: int, Scope: RecordScope, Catalog: EntityCatalog
) -> tuple[ClassSchema, ...]:
    Identity = Scope.ClassCodes[TypeCode]
    Stops = Scope.Continuations.get(ObjectId, frozenset()) - {Identity}
    return ClassGroups(Catalog, Identity, Stops)
