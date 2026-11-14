from convert.formats.Fusion.DocumentCodec.Materials.AssetDefaults import AssetDefaults
from convert.formats.Fusion.DocumentCodec.Materials.Model.AssetFamily import AssetFamily
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFields import SchemaFields
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


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
