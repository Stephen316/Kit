from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmNum,
    ReadAsmVec,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Geometry.Frustum.FrustumEvidence import (
    FrustumEvidence,
)


def ReadFrustum(Payload: bytes) -> FrustumEvidence:
    Table = ReadAsmTable(Payload)
    Surface = next(Record for Record in Table.Records if Record.Name == "cone-surface")
    Curves = [Record for Record in Table.Records if Record.Name == "ellipse-curve"]
    Curves.sort(key=lambda Record: ReadAsmVec(Record, 3, 19).z)
    if len(Curves) != 2:
        raise ValueError("Frustum evidence requires two circular boundaries")
    BasePoint = ReadAsmVec(Curves[0], 3, 19)
    TopPoint = ReadAsmVec(Curves[1], 3, 19)
    return FrustumEvidence(
        Table,
        ReadAsmVec(Curves[0], 5, 20).x,
        ReadAsmVec(Curves[1], 5, 20).x,
        TopPoint.z - BasePoint.z,
        BasePoint,
        ReadAsmNum(Surface, 9),
        ReadAsmNum(Surface, 10),
        ReadAsmNum(Surface, 11),
    )
