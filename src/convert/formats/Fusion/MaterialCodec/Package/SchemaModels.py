from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.Schema.CheckSchemas import (
    CheckSchemas,
)
from convert.formats.Fusion.MaterialCodec.Package.Schema.PropertyModel import (
    PropertyModel,
)
from convert.formats.Fusion.MaterialCodec.Package.Schema.SchemaIdentity import (
    SchemaIdentity,
)
from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas


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
