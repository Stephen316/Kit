from convert.Formats.Fusion.DocumentCodec.Materials.AssetDefaults import AssetDefaults
from convert.Formats.Fusion.DocumentCodec.Materials.Model.AssetFamily import AssetFamily
from convert.Formats.Fusion.DocumentCodec.Materials.SchemaFields import SchemaFields
from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


# the mat asset operation needs a consistent construction rule so appearance references remain connected to their owning entities
def BuildMatAsset(
    Family: AssetFamily,
    Nodes: dict[str, SchemaNode],
    Schemas: tuple[MaterialSchema, ...],
) -> MaterialAsset:
    Fields = SchemaFields(Family.SchemaName, Nodes)
    Definitions = AssetDefaults(Family.SchemaName, Fields, Schemas, True)
    Properties = AssetDefaults(Family.SchemaName, Fields, Schemas, False)
    for FieldName, TextValue in (
        ("BaseSchema", Family.SchemaName),
        ("UIName", Family.NameValue),
        ("VersionGUID", Family.DefinitionId),
    ):
        Definitions[FieldName] = PropertyValue(FieldName, TextValue)
    for Property in Family.Properties:
        if Property.FieldName not in Properties:
            raise ValueError("Authored material field is absent from its schema")
        Properties[Property.FieldName] = Property
    return MaterialAsset(
        Family.SchemaName,
        Family.InstanceId,
        Family.DefinitionId,
        Family.AssetRole,
        tuple(Definitions[NameValue] for NameValue in sorted(Definitions)),
        tuple(Properties[NameValue] for NameValue in sorted(Properties)),
    )
