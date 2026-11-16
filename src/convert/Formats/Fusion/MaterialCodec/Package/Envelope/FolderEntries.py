from convert.Formats.Fusion.MaterialCodec.Package.Envelope.EmitCore import EmitCore
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.EmitLinks import EmitLinks
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.EmitResources import (
    EmitResources,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)


# the folder entries contract needs a shared interpretation so typed appearance properties retain their native identifiers
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
