from convert.Formats.Fusion.DocumentCodec.Materials.ReadMatValue import ReadMatValue
from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.Formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.Formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields


# the asset defaults contract needs a shared interpretation so appearance references remain connected to their owning entities
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
