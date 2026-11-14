from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadCore import ReadCore
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadLinks import ReadLinks
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadResources import (
    ReadResources,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxFolderDepth,
    KMaxPackage,
    KMaxXmlBytes,
)
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckFolder import (
    CheckSegment,
)
from convert.formats.Fusion.MaterialCodec.Package.Xml.ReadGroup import ReadGroup


def ReadFolder(
    Archive: IndexedArchive, PathValue: str, FolderName: str, Depth: int
) -> PackageFolder:
    if Depth > KMaxFolderDepth:
        raise ValueError("Material resource folders exceed the depth limit")
    CoreValue = ReadCore(Archive.ReadMember(PathValue + "core.xml", KMaxXmlBytes))
    if CoreValue.NameValue != FolderName:
        raise ValueError("Material resource folder disagrees with its link")
    Payload = Archive.ReadMember(PathValue + "cnx.xml", KMaxXmlBytes)
    if all("class" in Child.attrib for Child in ReadGroup(Payload, "default")):
        Links = ReadResources(Payload)
        for LinkValue in Links:
            CheckSegment(LinkValue.FileName)
        return PackageFolder(
            CoreValue,
            Links=Links,
            Contents=tuple(
                Archive.ReadMember(PathValue + LinkValue.FileName, KMaxPackage)
                for LinkValue in Links
            ),
        )
    Names = ReadLinks(Payload)
    for NameValue in Names:
        CheckSegment(NameValue)
    return PackageFolder(
        CoreValue,
        tuple(
            ReadFolder(Archive, PathValue + NameValue + "/", NameValue, Depth + 1)
            for NameValue in Names
        ),
    )
