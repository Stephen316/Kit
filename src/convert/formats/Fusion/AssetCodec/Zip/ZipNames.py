# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from unicodedata import normalize as NormalizeText

from convert.formats.Fusion.AssetCodec.Zip.ZipLimits import (
    KMaxPathDepth,
    KMaxPathPart,
    KMaxZipName,
)

# regular zip files must remain regular files on case insensitive windows hosts
KDeviceNames = frozenset(
    ("aux", "con", "nul", "prn", "conin$", "conout$")
    + tuple(Family + Number for Family in ("com", "lpt") for Number in "123456789¹²³")
)

# portable names cannot alias local paths through reserved separators
KUnsafeChars = frozenset('<>:"\\|?*')


# a directory marker is the only trailing separator in a canonical member name
def EncodeZipName(NameValue: str) -> bytes:
    if (
        type(NameValue) is not str
        or not 0 < len(NameValue) <= KMaxZipName
        or not NameValue.isprintable()
        or not KUnsafeChars.isdisjoint(NameValue)
        or NormalizeText("NFC", NameValue) != NameValue
    ):
        raise ValueError("Unsafe or oversized Fusion ZIP member name")
    Parts = NameValue.removesuffix("/").split("/")
    if len(Parts) > KMaxPathDepth or any(
        not Section
        or Section.endswith((" ", "."))
        or len(Section.encode("utf-8")) > KMaxPathPart
        or Section.partition(".")[0].rstrip().casefold() in KDeviceNames
        for Section in Parts
    ):
        raise ValueError("Unsafe Fusion ZIP member path")
    NameBytes = NameValue.encode("utf-8")
    if len(NameBytes) > KMaxZipName:
        raise ValueError("Oversized Fusion ZIP member name")
    return NameBytes


# path conflicts must not change the meaning of a valid name during extraction
def CheckZipPaths(Names: tuple[str, ...]) -> None:
    Paths: dict[str, bool] = {}
    for NameValue in Names:
        PathKey = NameValue.removesuffix("/").casefold()
        if PathKey in Paths:
            raise ValueError("Duplicate Fusion ZIP member path")
        Paths[PathKey] = NameValue.endswith("/")
    for PathKey in Paths:
        Parent = PathKey.rpartition("/")[0]
        while Parent:
            if Paths.get(Parent) is False:
                raise ValueError("Fusion ZIP file is also a parent directory")
            Parent = Parent.rpartition("/")[0]
