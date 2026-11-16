from convert.Formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCoedge,
    KFirstPoint,
)

# first attribute must remain consistent across callers so profile topology remains connected to its extrusion history
KFirstAttribute = KFirstPoint + 8

# body generic must remain consistent across callers so profile topology remains connected to its extrusion history
KBodyGeneric = KFirstAttribute + 1

# first face tag must remain consistent across callers so profile topology remains connected to its extrusion history
KFirstFaceTag = KBodyGeneric + 1

# first sketch tag must remain consistent across callers so profile topology remains connected to its extrusion history
KFirstSketchTag = KFirstFaceTag + 6

# prism records must remain consistent across callers so profile topology remains connected to its extrusion history
KPrismRecords = KFirstSketchTag + 8

# the base edges order must stay explicit so profile topology remains connected to its extrusion history
KBaseEdges = (0, 5, 1, 4)

# sketch owners must remain consistent across callers so profile topology remains connected to its extrusion history
KSketchOwners = tuple(
    tuple(
        KFirstCoedge + Index
        for Index, Value in enumerate(BuildUses())
        if Value.EdgeIndex == EdgeIndex
    )
    for EdgeIndex in KBaseEdges
)
