from convert.formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxEntries,
    KMaxFolderDepth,
)
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckCore import CheckCore
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckResources import (
    CheckResources,
)

KReserved = ("", ".", "..", "cnx.xml", "core.xml")


def CheckSegment(NameValue: str) -> None:
    if (
        type(NameValue) is not str
        or NameValue in KReserved
        or any(Character in NameValue for Character in "/\\\x00")
    ):
        raise ValueError("Invalid material resource folder name")


def CheckFolder(Value: PackageFolder, Depth: int) -> None:
    if Depth > KMaxFolderDepth:
        raise ValueError("Material resource folders exceed the depth limit")
    CoreValue = Value.Core
    CheckCore(CoreValue)
    if (
        CoreValue.NameValue is None
        or CoreValue.EmbedOption is not None
        or CoreValue.LastSaved is not None
        or CoreValue.IsReadOnly is not None
    ):
        raise ValueError("Unsupported material folder metadata profile")
    CheckSegment(CoreValue.NameValue)
    if bool(Value.Folders) == bool(Value.Links) or not (
        len(Value.Folders) + len(Value.Links) <= KMaxEntries
    ):
        raise ValueError("Material resource folder needs folders or resources")
    if len(Value.Contents) != len(Value.Links) or any(
        type(Content) is not bytes for Content in Value.Contents
    ):
        raise ValueError("Material resource contents disagree with links")
    Names = tuple(LinkValue.FileName for LinkValue in Value.Links)
    for NameValue in Names:
        CheckSegment(NameValue)
    CheckResources(Value.Links, Names, "application/octet-stream")
    Children = tuple(Child.Core.NameValue for Child in Value.Folders)
    if len(set(Children)) != len(Children):
        raise ValueError("Duplicate material resource folder")
    for Child in Value.Folders:
        CheckFolder(Child, Depth + 1)
