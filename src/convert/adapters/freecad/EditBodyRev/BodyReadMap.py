# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.Native import NativeObject
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep

# one planar source prism has a small bounded naming table
KMaxAxisMap = 16384

# the source rim name expands through this native extrusion edge postfix
KRimPostfix = ";:Hb,E"


# saved topology naming must expand the chosen row to the authored sketch edge
def ReadRimShadow(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Native: NativeObject,
    Slot: int,
    GeoId: int,
    Sides: int,
) -> str:
    NameValue = f"{Native.name}.Shape.Map.txt"
    Shape = Native.properties["Shape"]
    Maps = Shape.findall("./ElementMap2")
    if len(Maps) != 1 or Maps[0].attrib != {"file": NameValue} or len(Maps[0]):
        raise ValueError("FreeCAD editable body axis source edge map is missing")
    DataValue = ReadEditBrep(
        Archive, Members, NameValue, KMaxAxisMap, "editable body edge map"
    )
    Rows = [
        Line.strip() for Line in DataValue.decode("ascii").splitlines() if Line.strip()
    ]
    if len(Rows) < 10 or Rows[0] != "BeginElementMap v1":
        raise ValueError("FreeCAD editable body axis source edge map header changed")
    Fields = Rows[1].split()
    if (
        len(Fields) != 3
        or Fields[1] != "PostfixCount"
        or not Fields[0].isdigit()
        or not Fields[2].isdigit()
    ):
        raise ValueError("FreeCAD editable body axis source edge map table changed")
    Count = int(Fields[2])
    if not 3 <= Count <= 256:
        raise ValueError("FreeCAD editable body axis source edge postfix count changed")
    Postfix = Rows[2 : 2 + Count]
    Names = Rows[2 + Count :]
    Header = [
        "MapCount 1",
        f"ElementMap 1 {Fields[0]} 3",
        "Edge",
        "ChildCount 0",
        f"NameCount {3 * Sides + 1}",
    ]
    if Names[: len(Header)] != Header or Postfix.count(KRimPostfix) != 1:
        raise ValueError("FreeCAD editable body axis source edge naming changed")
    Tag = f"$#b:{GeoId:x}.{Postfix.index(KRimPostfix) + 1:x}"
    EdgeRows = Names[len(Header) : len(Header) + 3 * Sides + 1]
    if (
        len(EdgeRows) != 3 * Sides + 1
        or EdgeRows[0] != "0"
        or not 0 < Slot < len(EdgeRows)
        or EdgeRows[Slot].split() != [Tag, "0"]
        or sum(Tag in Row.split() for Row in EdgeRows) != 1
    ):
        raise ValueError("FreeCAD editable body axis source edge map slot changed")
    Tail = Names[len(Header) + len(EdgeRows) :]
    for Kind, RowsCount in (("Face", Sides + 3), ("Vertex", 2 * Sides + 1)):
        if Tail[:4] != [Kind, "ChildCount 0", f"NameCount {RowsCount}", "0"]:
            raise ValueError(
                "FreeCAD editable body axis source edge map inventory changed"
            )
        Tail = Tail[3 + RowsCount :]
    if Tail != ["EndMap"]:
        raise ValueError(
            "FreeCAD editable body axis source edge map has additional data"
        )
    return f";#b:{GeoId:x}{KRimPostfix}.Edge{Slot}"
