from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


# boundary representation wire needs an explicit state contract so topology identity survives native history reconstruction
@MakeDataClass(frozen=True, slots=True)
class BrepWire:
    Header: BrepHeader
    Stamp: GeometryStamp
    Table: AsmTable
    Journal: tuple[AsmRecord, ...]
