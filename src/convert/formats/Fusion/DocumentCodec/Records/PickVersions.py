from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.formats.Fusion.EntityCodec.Vocabulary.OpaqueSchema import OpaqueSchema
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def PickVersions(
    Schemas: tuple[ClassSchema, ...], Classes: tuple[MetaClass, ...]
) -> tuple[ClassSchema, ...]:
    Declared = {Entry.ClassGuid.upper(): Entry for Entry in Classes}
    Grouped: dict[str, list[ClassSchema]] = {}
    for Schema in Schemas:
        Grouped.setdefault(Schema.ClassGuid.upper(), []).append(Schema)
    Result: list[ClassSchema] = []
    for Identity, Versions in Grouped.items():
        Entry = Declared.get(Identity)
        if Entry is None:
            Result.append(max(Versions, key=lambda Schema: Schema.SchemaVersion))
            continue
        Exact = tuple(
            Schema
            for Schema in Versions
            if Schema.SchemaVersion == Entry.SchemaVersion
            and Schema.BaseGuid.upper() == Entry.BaseGuid.upper()
        )
        Result.append(Exact[0] if Exact else OpaqueSchema(Entry))
    Result.extend(
        OpaqueSchema(Entry)
        for Identity, Entry in Declared.items()
        if Identity not in Grouped
    )
    return DropOrphans(tuple(Result), frozenset(Declared))


def DropOrphans(
    Schemas: tuple[ClassSchema, ...], Declared: frozenset[str]
) -> tuple[ClassSchema, ...]:
    Result = Schemas
    while True:
        Present = {Schema.ClassGuid.upper() for Schema in Result}
        Retained = tuple(
            Schema
            for Schema in Result
            if Schema.ClassGuid.upper() in Declared
            or not Schema.BaseGuid
            or Schema.BaseGuid.upper() in Present | {KNativeRoot}
        )
        if len(Retained) == len(Result):
            return Result
        Result = Retained
