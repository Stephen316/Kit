# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import BadZipFile, ZipFile, ZipInfo

from convert.adapters.freecad.Archive import KDocEntry, KManifestEntry

# native view and thumbnail records do not carry independent authored shapes
KDatumAuxFiles = frozenset(
    {
        KDocEntry,
        KManifestEntry,
        "GuiDocument.xml",
        "thumbnails/Thumbnail.png",
    }
)


# standalone datum archives may carry only the original source and native display data
def CheckDatumFiles(
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Entries: Mapping[str, bytes],
) -> None:
    Files = {NameValue for NameValue, Entry in Members.items() if not Entry.is_dir()}
    if (
        Files - Entries.keys() - KDatumAuxFiles
        or any(NameValue.lower().endswith((".brp", ".brep")) for NameValue in Files)
        or any(Value.get("file") for Value in RootValue.findall(".//*[@file]"))
    ):
        raise ValueError("FreeCAD editable datum has unexpected native data")
    for NameValue in Entries.keys() & Files:
        DataValue = Entries[NameValue]
        try:
            if (
                Members[NameValue].file_size != len(DataValue)
                or Archive.read(Members[NameValue]) != DataValue
            ):
                raise ValueError("FreeCAD editable datum source payload changed")
        except (BadZipFile, OSError, RuntimeError) as ErrorInfo:
            raise ValueError(
                "FreeCAD editable datum source payload is unreadable"
            ) from ErrorInfo
