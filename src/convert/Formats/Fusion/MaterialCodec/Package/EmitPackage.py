from convert.Formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.Formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.Formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.PackageEntries import (
    PackageEntries,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxPackage,
    KStreamNames,
    KVersionTable,
)
from convert.Formats.Fusion.MaterialCodec.Package.Schema.EmitSchemaNode import (
    EmitSchemaNode,
)
from convert.Formats.Fusion.MaterialCodec.Package.Schema.SchemaIdentity import (
    SchemaIdentity,
)
from convert.Formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels
from convert.Formats.Fusion.MaterialCodec.Package.Validation.CheckPackage import (
    CheckPackage,
)


# the package operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def EmitPackage(Value: MaterialPackage) -> bytes:
    CheckPackage(Value)
    Streams = EncodeMaterials(Value.Assets, SchemaModels(Value.Schemas))
    Prefix = Value.AssetCore.Identifier + "/"
    Members = PackageEntries(Value)
    Members.update(
        {
            Prefix + "AssetData/" + NameValue: Content
            for NameValue, Content in zip(
                KStreamNames,
                (
                    Streams.TableData,
                    Streams.DefinitionData,
                    Streams.InstanceData,
                    KVersionTable,
                ),
                strict=True,
            )
        }
    )
    Members.update(
        {
            Prefix
            + "Schemas/"
            + SchemaIdentity(Schema)
            + ".xml": EmitSchemaNode(Schema)
            for Schema in Value.Schemas
        }
    )
    if sum(len(Content) for Content in Members.values()) > KMaxPackage:
        raise ValueError("Material package expansion exceeds size limit")
    Payload = EmitAssetZip(
        tuple(
            ZipAssetRow(NameValue, Content, False)
            for NameValue, Content in Members.items()
        )
    )
    if len(Payload) > KMaxPackage:
        raise ValueError("Material package exceeds size limit")
    return Payload
