from convert.formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from convert.formats.Fusion.MaterialCodec.Package.Envelope.PackageEntries import (
    PackageEntries,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxPackage,
    KStreamNames,
    KVersionTable,
)
from convert.formats.Fusion.MaterialCodec.Package.Schema.EmitSchemaNode import (
    EmitSchemaNode,
)
from convert.formats.Fusion.MaterialCodec.Package.Schema.SchemaIdentity import (
    SchemaIdentity,
)
from convert.formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckPackage import (
    CheckPackage,
)


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
