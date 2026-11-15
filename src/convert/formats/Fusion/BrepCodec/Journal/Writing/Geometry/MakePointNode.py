from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import PointWord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


# the point node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakePointNode(Value: PointNode) -> AsmRecord:
    return AsmRecord(
        "point",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.PositionCm),
        ),
    )
