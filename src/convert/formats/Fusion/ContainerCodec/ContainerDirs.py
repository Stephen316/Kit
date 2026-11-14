from convert.formats.Fusion.ContainerCodec.ContainerLayout import (
    KAssetPrefix,
    KPartFolders,
)
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.ContainerCodec.PartDirs import PartDirs


def ContainerDirs(Value: FusionContainer, Folders: tuple[str, ...]) -> set[str]:
    if (
        type(Value.EmptyFolders) is not tuple
        or any(
            type(Folder) is not str or Folder not in KPartFolders
            for Folder in Value.EmptyFolders
        )
        or len(set(Value.EmptyFolders)) != len(Value.EmptyFolders)
    ):
        raise ValueError("Invalid Fusion container empty folders")
    PartFolders = {PartValue.Name.partition("/")[0] for PartValue in Value.Parts}
    if (
        PartFolders.intersection(Value.EmptyFolders)
        or "Breps.BlobParts" in Value.EmptyFolders
    ):
        raise ValueError("Fusion empty folders duplicate generated directories")
    Directories = {KAssetPrefix, KAssetPrefix + "Breps.BlobParts/"}
    if Value.Previews:
        Directories.add(KAssetPrefix + "Previews/")
    Directories.update(KAssetPrefix + Folder for Folder in Folders)
    Directories.update(
        KAssetPrefix + Folder + "/" for Folder in (*PartFolders, *Value.EmptyFolders)
    )
    Directories.update(PartDirs(Value.Parts))
    return Directories
