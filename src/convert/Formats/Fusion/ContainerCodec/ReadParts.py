from convert.Formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.Formats.Fusion.ContainerCodec.IsGraphicPath import IsGraphicPath
from convert.Formats.Fusion.AssetCodec.Zip.ZipLimits import KMaxMemberBytes
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import (
    KAssetPrefix,
    KPartFolders,
    KPreviewNames,
)
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart


# the parts operation needs a distinct decoding boundary so archive members retain their native ownership and reference relationships
def ReadParts(
    Archive: IndexedArchive,
) -> tuple[tuple[ContainerPart, ...], tuple[str, ...]]:
    Parts: list[ContainerPart] = []
    Folders: set[str] = set()
    Filled: set[str] = {"Breps.BlobParts"}
    for Entry in Archive.Members:
        if not Entry.Name.startswith(KAssetPrefix):
            continue
        Relative = Entry.Name.removeprefix(KAssetPrefix)
        Sections = Relative.split("/")
        if (len(Sections) != 2 and not IsGraphicPath(Relative)) or Sections[
            0
        ] not in KPartFolders:
            continue
        if Entry.IsDirectory:
            Folders.add(Sections[0])
        elif Relative not in KPreviewNames:
            Parts.append(
                ContainerPart(Relative, Archive.ReadMember(Entry.Name, KMaxMemberBytes))
            )
            Filled.add(Sections[0])
    return tuple(Parts), tuple(sorted(Folders - Filled))
