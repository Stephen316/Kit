from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# field cursor needs an explicit state contract so revision ownership survives native history reconstruction
@MakeDataClass(slots=True)
class FieldCursor:
    Record: AsmRecord
    Offset: int = 0
