from typing import cast as CastValue
from convert.formats.Fusion.ContainerCodec.IsGraphicPath import IsGraphicPath

from convert.formats.Fusion.AssetCodec.Zip.ZipLimits import (
    KMaxMemberBytes,
    KMaxZipEntries,
)
from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths, EncodeZipName
from convert.formats.Fusion.ContainerCodec.ContainerLayout import (
    KPartFolders,
    KPreviewNames,
)
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Preview.CheckPreview import CheckPreview


def CheckParts(Values: tuple[ContainerPart, ...], *, IsPreview: bool = False) -> None:
    if type(Values) is not tuple or len(Values) > KMaxZipEntries:
        raise ValueError("Invalid Fusion container parts")
    Names: list[str] = []
    for Entry in Values:
        if (
            not isinstance(CastValue(object, Entry), ContainerPart)
            or type(Entry.Payload) is not bytes
            or len(Entry.Payload) > KMaxMemberBytes
        ):
            raise ValueError("Invalid Fusion container part")
        _ = EncodeZipName(Entry.Name)
        Sections = Entry.Name.split("/")
        if (
            (len(Sections) != 2 and (IsPreview or not IsGraphicPath(Entry.Name)))
            or not Sections[1]
            or (
                Entry.Name not in KPreviewNames
                if IsPreview
                else Sections[0] not in KPartFolders
            )
        ):
            raise ValueError("Unsupported Fusion container part path")
        if IsPreview:
            CheckPreview(Entry.Payload)
        Names.append(Entry.Name)
    CheckZipPaths(tuple(Names))
