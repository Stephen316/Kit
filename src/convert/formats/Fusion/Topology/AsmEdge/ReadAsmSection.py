from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmLocation import AsmLocation
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmRecord,
    ReadAsmName,
    ReadAsmRecord,
)


# the section sentinel delimits geometry without assigning a timeline state to any record
def ReadAsmSection(
    Cursor: MetaCursor, Sentinel: str
) -> tuple[tuple[AsmRecord, ...], tuple[AsmLocation, ...]]:
    Records: list[AsmRecord] = []
    Locations: list[AsmLocation] = []
    for _ in range(8192):
        StartOffset = Cursor.Offset
        NameValue = ReadAsmName(Cursor)
        if NameValue == Sentinel:
            return tuple(Records), tuple(Locations)
        if NameValue in (
            "Begin-of-ASM-History-Data",
            "End-of-ASM-History-Section",
            "End-of-ASM-data",
            "history_stream",
            "delta_state",
        ):
            raise ValueError("Unexpected Fusion ASM section boundary")
        Records.append(ReadAsmRecord(Cursor, NameValue))
        Locations.append(AsmLocation(StartOffset, Cursor.Offset))
    raise ValueError("Oversized Fusion ASM history geometry table")
