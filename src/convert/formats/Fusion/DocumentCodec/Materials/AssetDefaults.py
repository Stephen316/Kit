from convert.formats.Fusion.DocumentCodec.Materials.ReadMatValue import ReadMatValue
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields


def AssetDefaults(
    NameValue: str,
    Fields: dict[str, SchemaNode],
    Schemas: tuple[MaterialSchema, ...],
    IsDefinition: bool,
) -> dict[str, PropertyValue]:
    Selected = SelectFields(BuildSchemas(Schemas)[NameValue], IsDefinition)
    return {
        Field.FieldName: PropertyValue(
            Field.FieldName, ReadMatValue(Fields[Field.FieldName])
        )
        for Field in Selected
    }
