from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.Formats.Fusion.MaterialCodec.Package.Schema.CheckSchemas import (
    CheckSchemas,
)
from convert.Formats.Fusion.MaterialCodec.Package.Schema.PropertyModel import (
    PropertyModel,
)
from convert.Formats.Fusion.MaterialCodec.Package.Schema.SchemaIdentity import (
    SchemaIdentity,
)
from convert.Formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas


# the schema models contract needs a shared interpretation so typed appearance properties retain their native identifiers
def SchemaModels(Schemas: tuple[SchemaNode, ...]) -> tuple[MaterialSchema, ...]:
    CheckSchemas(Schemas)
    Models = tuple(
        MaterialSchema(
            SchemaIdentity(Schema),
            tuple(
                dict(Child.Attributes)["val"]
                for Child in Schema.Children
                if Child.TagName == "Base"
            ),
            tuple(
                PropertyModel(Child)
                for Child in Schema.Children
                if "id" in dict(Child.Attributes) and Child.TagName != "PropertyAlias"
            ),
        )
        for Schema in Schemas
    )
    _ = BuildSchemas(Models)
    return Models
