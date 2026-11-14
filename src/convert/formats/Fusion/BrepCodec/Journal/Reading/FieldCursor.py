from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


@MakeDataClass(slots=True)
class FieldCursor:
    Record: AsmRecord
    Offset: int = 0
