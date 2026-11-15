from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the prefix operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakePrefix(Value: EntityPrefix) -> tuple[KAsmToken, ...]:
    return (12, Value.Attribute), (4, Value.EntityTag), (12, -1)
