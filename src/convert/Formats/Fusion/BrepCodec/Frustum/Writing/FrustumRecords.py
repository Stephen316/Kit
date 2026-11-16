from dataclasses import replace as Replace

from convert.Formats.Fusion.BrepCodec.Attributes.HistoryAttributes import (
    MakeHistoryTags,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumCoedges import (
    FrustumCoedges,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumCurves import FrustumCurves
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumEdges import FrustumEdges
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumPlanes import FrustumPlanes
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumPoints import FrustumPoints
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumSurface import (
    FrustumSurface,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumVertices import (
    FrustumVertices,
)
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Topology.ApplyIds import ApplyIds
from convert.Formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.Formats.Fusion.BrepCodec.Topology.HistoryLinks import KHistoryHeads
from convert.Formats.Fusion.GeometryCodec.CylinderFaces import BuildFaces
from convert.Formats.Fusion.GeometryCodec.CylinderLoops import BuildLoops
from convert.Formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the frustum records contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumRecords(
    Identity: BodyIdentity,
    TagSet: TopologyTags,
    Frame: FrustumFrame,
    Tracking: EntityIds | None = None,
) -> tuple[GeometryRecord, ...]:
    PlainRecords = (
        *BuildRoots(),
        *BuildFaces(),
        *BuildLoops(),
        *FrustumCoedges(Frame),
        *FrustumEdges(Frame),
        FrustumSurface(Frame.Surface),
        *FrustumPlanes(Frame),
        *FrustumVertices(Frame),
        *FrustumCurves(Frame),
        *FrustumPoints(Frame),
    )
    Records = list(
        AssignHeads(ApplyIds(PlainRecords, Tracking or EntityIds()), KHistoryHeads)
    )
    BodyRoot = Records[1]
    Records[1] = Replace(
        BodyRoot, Fields=(BodyRoot.Fields[0], Identity.BodyKey, *BodyRoot.Fields[2:])
    )
    return (*Records, *MakeHistoryTags(Identity, TagSet))
