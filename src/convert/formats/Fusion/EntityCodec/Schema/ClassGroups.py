from convert.formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog

KNoStops: frozenset[str] = frozenset()


def ClassGroups(
    Catalog: EntityCatalog, ClassGuid: str, Stops: frozenset[str] = KNoStops
) -> tuple[ClassSchema, ...]:
    Groups: list[ClassSchema] = []
    Visited: set[str] = set()
    Identity = ClassGuid.upper()
    while Identity and Identity != Catalog.RootGuid and Identity not in Stops:
        if Identity in Visited or len(Visited) >= KMaxDepth:
            raise ValueError("Cyclic or excessively deep Fusion entity inheritance")
        if Identity not in Catalog.Classes:
            raise ValueError("Fusion entity profile is missing an inherited class")
        Visited.add(Identity)
        Schema = Catalog.Classes[Identity]
        Groups.append(Schema)
        if Schema.IsOpaque:
            break
        Identity = Schema.BaseGuid.upper()
    return tuple(Groups)
