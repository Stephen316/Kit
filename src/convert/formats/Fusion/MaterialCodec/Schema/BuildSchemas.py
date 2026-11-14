from convert.formats.Fusion.MaterialCodec.Limits import KMaxCount
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Schema.CheckProperty import CheckProperty
from convert.formats.Fusion.MaterialCodec.Schema.ResolveBasesMut import ResolveBasesMut
from convert.formats.Fusion.MaterialCodec.Schema.SchemaTable import KSchemaTable
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def BuildSchemas(Schemas: tuple[MaterialSchema, ...]) -> KSchemaTable:
    if not 1 <= len(Schemas) <= KMaxCount:
        raise ValueError("Fusion material schemas exceed the count limit")
    Declared = {Schema.SchemaName: Schema for Schema in Schemas}
    if len(Declared) != len(Schemas):
        raise ValueError("Duplicate Fusion material schema identifier")
    for Schema in Schemas:
        if not Schema.SchemaName or not EncodeText(Schema.SchemaName):
            raise ValueError("Fusion material schema requires an identifier")
        if len(Schema.Bases) != len(set(Schema.Bases)):
            raise ValueError("Duplicate Fusion material base schema")
        if len(Schema.Bases) > KMaxCount or len(Schema.Properties) > KMaxCount:
            raise ValueError("Fusion material schema exceeds the count limit")
        Names = {Field.FieldName for Field in Schema.Properties}
        if len(Names) != len(Schema.Properties):
            raise ValueError("Duplicate Fusion material schema property")
        for Field in Schema.Properties:
            CheckProperty(Field)
    Resolved: KSchemaTable = {}
    for Schema in Schemas:
        _ = ResolveBasesMut(Schema.SchemaName, Declared, Resolved)
    return Resolved
