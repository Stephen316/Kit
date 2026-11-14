from convert.formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCoedge,
    KFirstPoint,
)

KFirstAttribute = KFirstPoint + 8
KBodyGeneric = KFirstAttribute + 1
KFirstFaceTag = KBodyGeneric + 1
KFirstSketchTag = KFirstFaceTag + 6
KPrismRecords = KFirstSketchTag + 8
KBaseEdges = (0, 5, 1, 4)
KSketchOwners = tuple(
    tuple(
        KFirstCoedge + Index
        for Index, Value in enumerate(BuildUses())
        if Value.EdgeIndex == EdgeIndex
    )
    for EdgeIndex in KBaseEdges
)
