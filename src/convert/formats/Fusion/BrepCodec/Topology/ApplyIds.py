from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord

# the face ordinals order must stay explicit so topology identity survives native history reconstruction
KFaceOrdinals = (4, 5, 6)

# the vertex ordinals order must stay explicit so topology identity survives native history reconstruction
KVertexOrdinals = (20, 21)


# apply ids needs an explicit validity boundary so topology identity survives native history reconstruction
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
