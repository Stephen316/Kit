from convert.Formats.Fusion.MaterialCodec.Package.Envelope.EmitCore import EmitCore
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.EmitLinks import EmitLinks
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.EmitResources import (
    EmitResources,
)
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.FolderEntries import (
    FolderEntries,
)
from convert.Formats.Fusion.MaterialCodec.Package.Envelope.FormatEntries import (
    FormatEntries,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import KFolderSets


# the package entries contract needs a shared interpretation so typed appearance properties retain their native identifiers
def PackageEntries(Value: MaterialPackage) -> dict[str, bytes]:
    Prefix = Value.AssetCore.Identifier + "/"
    Folders = KFolderSets[0] if Value.Resources is None else KFolderSets[1]
    Result = FormatEntries()
    Result.update(
        {
            "cnx.xml": EmitLinks((Value.AssetCore.Identifier,)),
            "core.xml": EmitCore(Value.RootCore),
            Prefix + "cnx.xml": EmitLinks(Folders),
            Prefix + "core.xml": EmitCore(Value.AssetCore),
            Prefix + "AssetData/core.xml": EmitCore(Value.DataCore),
            Prefix + "Schemas/core.xml": EmitCore(Value.SchemaCore),
            Prefix + "AssetData/cnx.xml": EmitResources(Value.DataLinks),
            Prefix + "Schemas/cnx.xml": EmitResources(Value.SchemaLinks),
        }
    )
    if Value.Resources is not None:
        Result.update(FolderEntries(Value.Resources, Prefix + "Resources/"))
    return Result
