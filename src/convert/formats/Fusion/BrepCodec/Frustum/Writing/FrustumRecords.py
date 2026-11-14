from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Attributes.HistoryAttributes import (
    MakeHistoryTags,
)
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumCoedges import (
    FrustumCoedges,
)
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumCurves import FrustumCurves
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumEdges import FrustumEdges
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumPlanes import FrustumPlanes
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumPoints import FrustumPoints
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumSurface import (
    FrustumSurface,
)
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumVertices import (
    FrustumVertices,
)
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Topology.ApplyIds import ApplyIds
from convert.formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.formats.Fusion.BrepCodec.Topology.HistoryLinks import KHistoryHeads
from convert.formats.Fusion.GeometryCodec.CylinderFaces import BuildFaces
from convert.formats.Fusion.GeometryCodec.CylinderLoops import BuildLoops
from convert.formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


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
