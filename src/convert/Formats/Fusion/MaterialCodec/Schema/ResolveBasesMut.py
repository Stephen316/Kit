from convert.Formats.Fusion.MaterialCodec.Limits import KMaxCount
from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Schema.SchemaTable import KSchemaTable


# resolve bases needs an explicit validity boundary so typed appearance properties retain their native identifiers
def ResolveBasesMut(
    SchemaName: str,
    Declared: dict[str, MaterialSchema],
    ResolvedMut: KSchemaTable,
    Ancestors: tuple[str, ...] = (),
) -> tuple[PropertySpec, ...]:
    if SchemaName in ResolvedMut:
        return ResolvedMut[SchemaName]
    if SchemaName in Ancestors or len(Ancestors) >= 64:
        raise ValueError("Cyclic or excessively deep Fusion material schemas")
    if SchemaName not in Declared:
        raise ValueError("Missing Fusion material base schema")
    Schema = Declared[SchemaName]
    Fields: dict[str, PropertySpec] = {}
    for BaseName in Schema.Bases:
        BaseFields = ResolveBasesMut(
            BaseName, Declared, ResolvedMut, (*Ancestors, SchemaName)
        )
        Fields.update((Field.FieldName, Field) for Field in BaseFields)
    Fields.update((Field.FieldName, Field) for Field in Schema.Properties)
    if len(Fields) > KMaxCount:
        raise ValueError("Fusion material schema exceeds the property limit")
    ResolvedMut[SchemaName] = tuple(Fields[FieldName] for FieldName in sorted(Fields))
    return ResolvedMut[SchemaName]
