from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


@MakeDataClass(frozen=True, slots=True)
class BrepWire:
    Header: BrepHeader
    Stamp: GeometryStamp
    Table: AsmTable
    Journal: tuple[AsmRecord, ...]
