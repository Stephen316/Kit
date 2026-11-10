# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
    SlotValue: int,
    GeoId: int,
    Sides: int,
) -> str:
    NameValue = f"{Native.name}.Shape.Map.txt"
    Shape = Native.properties["Shape"]
    Mappings = Shape.findall("./ElementMap2")
    if (
        len(Mappings) != 1
        or Mappings[0].attrib != {"file": NameValue}
        or len(Mappings[0])
    ):
        raise ValueError("FreeCAD editable body axis source edge map is missing")
    DataValue = ReadEditBrep(
        Archive, Members, NameValue, KMaxAxisMap, "editable body edge map"
    )
    RowValues = [
        LineValue.strip()
        for LineValue in DataValue.decode("ascii").splitlines()
        if LineValue.strip()
    ]
    if len(RowValues) < 10 or RowValues[0] != "BeginElementMap v1":
        raise ValueError("FreeCAD editable body axis source edge map header changed")
    Fields = RowValues[1].split()
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
    Postfix = RowValues[2 : 2 + Count]
    Names = RowValues[2 + Count :]
    Header = [
        "MapCount 1",
        f"ElementMap 1 {Fields[0]} 3",
        "Edge",
        "ChildCount 0",
        f"NameCount {3 * Sides + 1}",
    ]
    if Names[: len(Header)] != Header or Postfix.count(KRimPostfix) != 1:
        raise ValueError("FreeCAD editable body axis source edge naming changed")
    TagValue = f"$#b:{GeoId:x}.{Postfix.index(KRimPostfix) + 1:x}"
    EdgeRows = Names[len(Header) : len(Header) + 3 * Sides + 1]
    if (
        len(EdgeRows) != 3 * Sides + 1
        or EdgeRows[0] != "0"
        or not 0 < SlotValue < len(EdgeRows)
        or EdgeRows[SlotValue].split() != [TagValue, "0"]
        or sum(TagValue in RowValue.split() for RowValue in EdgeRows) != 1
    ):
        raise ValueError("FreeCAD editable body axis source edge map slot changed")
    CheckMapTail(Names[len(Header) + len(EdgeRows) :], Sides)
    return f";#b:{GeoId:x}{KRimPostfix}.Edge{SlotValue}"


# face and vertex map tails must match the exact declared inventory
def CheckMapTail(TailValue: list[str], Sides: int) -> None:
    for KindValue, RowsCount in (("Face", Sides + 3), ("Vertex", 2 * Sides + 1)):
        if TailValue[:4] != [KindValue, "ChildCount 0", f"NameCount {RowsCount}", "0"]:
            raise ValueError(
                "FreeCAD editable body axis source edge map inventory changed"
            )
        TailValue = TailValue[3 + RowsCount :]
    if TailValue != ["EndMap"]:
        raise ValueError(
            "FreeCAD editable body axis source edge map has additional data"
        )
