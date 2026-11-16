from convert.Formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.Formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.Formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.ReadCore import ReadCore
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.ReadResources import (
    ReadResources,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxPackage,
    KMaxSchemas,
    KMaxXmlBytes,
    KVersionTable,
)
from convert.Formats.Fusion.MaterialCodec.Package.Reading.ReadFolder import ReadFolder
from convert.Formats.Fusion.MaterialCodec.Package.Schema.ReadSchemaNode import (
    ReadSchemaNode,
)
from convert.Formats.Fusion.MaterialCodec.Package.Schema.SchemaIdentity import (
    SchemaIdentity,
)
from convert.Formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels


# the package body operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def ReadPackageBody(
    Archive: IndexedArchive, Prefix: str, HasResources: bool
) -> MaterialPackage:
    SchemaLinks = ReadResources(
        Archive.ReadMember(Prefix + "Schemas/cnx.xml", KMaxXmlBytes)
    )
    if not 0 < len(SchemaLinks) <= KMaxSchemas or len(
        {LinkValue.FileName for LinkValue in SchemaLinks}
    ) != len(SchemaLinks):
        raise ValueError("Invalid or duplicate material schema resources")
    if any(
        "/" in LinkValue.FileName
        or "\\" in LinkValue.FileName
        or not LinkValue.FileName.endswith(".xml")
        for LinkValue in SchemaLinks
    ):
        raise ValueError("Invalid material schema resource path")
    Schemas = tuple(
        ReadSchemaNode(
            Archive.ReadMember(Prefix + "Schemas/" + LinkValue.FileName, KMaxXmlBytes)
        )
        for LinkValue in SchemaLinks
    )
    if any(
        LinkValue.FileName != SchemaIdentity(Schema) + ".xml"
        for LinkValue, Schema in zip(SchemaLinks, Schemas, strict=True)
    ):
        raise ValueError("Material schema resource disagrees with UID")
    StreamRoot = Prefix + "AssetData/"
    if Archive.ReadMember(StreamRoot + "StreamVersionTable", 1024) != KVersionTable:
        raise ValueError("Unsupported material stream versions")
    Streams = MaterialData(
        Archive.ReadMember(StreamRoot + "AssetTableOfContents.bin", KMaxPackage),
        Archive.ReadMember(
            StreamRoot + "DefinitionIteratorProperties.bin", KMaxPackage
        ),
        Archive.ReadMember(StreamRoot + "InstanceProperties.bin", KMaxPackage),
    )
    return MaterialPackage(
        ReadCore(Archive.ReadMember("core.xml", KMaxXmlBytes)),
        ReadCore(Archive.ReadMember(Prefix + "core.xml", KMaxXmlBytes)),
        ReadCore(Archive.ReadMember(StreamRoot + "core.xml", KMaxXmlBytes)),
        ReadCore(Archive.ReadMember(Prefix + "Schemas/core.xml", KMaxXmlBytes)),
        ReadResources(Archive.ReadMember(StreamRoot + "cnx.xml", KMaxXmlBytes)),
        SchemaLinks,
        Schemas,
        DecodeMaterials(Streams, SchemaModels(Schemas)),
        (
            ReadFolder(Archive, Prefix + "Resources/", "Resources", 0)
            if HasResources
            else None
        ),
    )
