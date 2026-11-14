from dataclasses import replace as Replace

from convert.formats.Fusion.AssetCodec.Zip.ZipHeaders import (
    KDirectoryAttr,
    KRegularAttr,
    KZipCreator,
    KZipUtfFlag,
)
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KDirExtract,
    KFileExtract,
    KFolderOrder,
    KStoredMethod,
    KZstdMethod,
)
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import (
    KAssetManifest,
    KPropertiesName,
    KReferenceName,
    KRootManifest,
    KSheetName,
)
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


def BuildLayout(
    Prefix: str,
    Members: tuple[str, ...],
    FolderOrder: tuple[str, ...],
    StampWords: tuple[int, int],
) -> tuple[PackageSlot, ...]:
    CheckFolders(Members, FolderOrder)
    TimeWord, DateWord = StampWords
    Folder = EntryLayout(
        KStoredMethod,
        KZipUtfFlag,
        TimeWord,
        DateWord,
        KZipCreator,
        KDirExtract,
        KDirectoryAttr,
    )
    Packed = Replace(
        Folder, Method=KZstdMethod, Extract=KFileExtract, Attributes=KRegularAttr
    )
    Stored = Replace(Packed, Method=KStoredMethod)
    return (
        PackageSlot(Prefix, Folder),
        *(PackageSlot(Prefix + NameValue, Folder) for NameValue in FolderOrder),
        PackageSlot(KRootManifest, Packed),
        PackageSlot(KPropertiesName, Packed),
        PackageSlot(KReferenceName, Stored),
        PackageSlot(Prefix + KSheetName, Packed),
        PackageSlot(Prefix + KAssetManifest, Packed),
        *(
            PackageSlot(Prefix + NameValue, Packed)
            for FolderName in FolderOrder
            for NameValue in Members
            if NameValue.startswith(FolderName)
        ),
    )


def CheckFolders(Members: tuple[str, ...], FolderOrder: tuple[str, ...]) -> None:
    if len(FolderOrder) != len(KFolderOrder) or set(FolderOrder) != set(KFolderOrder):
        raise ValueError("Fusion drawing folder order must permute the known folders")
    if any(NameValue.split("/")[0] + "/" not in FolderOrder for NameValue in Members):
        raise ValueError("Fusion drawing member lies outside the known folders")


def FolderParts(
    Parts: tuple[ContainerPart, ...], FolderOrder: tuple[str, ...]
) -> tuple[ContainerPart, ...]:
    return tuple(
        PartValue
        for FolderName in FolderOrder
        for PartValue in Parts
        if PartValue.Name.startswith(FolderName)
    )
