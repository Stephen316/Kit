from convert.formats.Fusion.MaterialCodec.Package.Envelope.EmitCore import EmitCore
from convert.formats.Fusion.MaterialCodec.Package.Envelope.EmitLinks import EmitLinks
from convert.formats.Fusion.MaterialCodec.Package.Envelope.EmitResources import (
    EmitResources,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)


def FolderEntries(Value: PackageFolder, PathValue: str) -> dict[str, bytes]:
    Result = {PathValue + "core.xml": EmitCore(Value.Core)}
    if Value.Links:
        Result[PathValue + "cnx.xml"] = EmitResources(Value.Links)
        Result.update(
            {
                PathValue + LinkValue.FileName: Content
                for LinkValue, Content in zip(Value.Links, Value.Contents, strict=True)
            }
        )
        return Result
    Names = tuple(str(Child.Core.NameValue) for Child in Value.Folders)
    Result[PathValue + "cnx.xml"] = EmitLinks(Names)
    for NameValue, Child in zip(Names, Value.Folders, strict=True):
        Result.update(FolderEntries(Child, PathValue + NameValue + "/"))
    return Result
