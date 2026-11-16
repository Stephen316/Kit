from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import KStreamNames
from convert.Formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels
from convert.Formats.Fusion.MaterialCodec.Package.Validation.CheckCoreRoles import (
    CheckCoreRoles,
)
from convert.Formats.Fusion.MaterialCodec.Package.Validation.CheckFolder import (
    CheckFolder,
)
from convert.Formats.Fusion.MaterialCodec.Package.Validation.CheckResources import (
    CheckResources,
)
from convert.Formats.Fusion.MaterialCodec.Records.CheckAssets import CheckAssets
from convert.Formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas


# invalid package input must fail here so typed appearance properties retain their native identifiers
def CheckPackage(Value: MaterialPackage) -> None:
    CheckCoreRoles(Value)
    Schemas = SchemaModels(Value.Schemas)
    CheckResources(Value.DataLinks, KStreamNames, "application/octet-stream")
    CheckResources(
        Value.SchemaLinks,
        tuple(Schema.SchemaName + ".xml" for Schema in Schemas),
        "application/xml",
    )
    CheckAssets(Value.Assets, BuildSchemas(Schemas))
    if Value.Resources is not None:
        if Value.Resources.Core.NameValue != "Resources":
            raise ValueError("Unsupported material resource folder")
        CheckFolder(Value.Resources, 0)
