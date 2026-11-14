from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord

KFaceOrdinals = (4, 5, 6)
KVertexOrdinals = (20, 21)


def ApplyIds(
    Records: tuple[GeometryRecord, ...], Tracking: EntityIds
) -> tuple[GeometryRecord, ...]:
    Results = list(Records)
    Pairs = (
        *zip(KFaceOrdinals, Tracking.FaceIds, strict=True),
        *zip(KVertexOrdinals, Tracking.VertexIds, strict=True),
    )
    for Ordinal, IdValue in Pairs:
        Current = Results[Ordinal]
        if Current.Fields[1] != -1:
            raise ValueError("Fusion BRep entity identity slot is already assigned")
        Results[Ordinal] = Replace(
            Current, Fields=(Current.Fields[0], IdValue, *Current.Fields[2:])
        )
    return tuple(Results)
