from dataclasses import replace as Replace

from convert.Formats.Fusion.BrepCodec.Attributes.HistoryAttributes import (
    MakeHistoryTags,
)
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.BrepCodec.Topology.ApplyIds import ApplyIds
from convert.Formats.Fusion.BrepCodec.Topology.ApplyVertices import ApplyVertices
from convert.Formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.Formats.Fusion.BrepCodec.Topology.HistoryLinks import KHistoryHeads
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderRecords import BuildRecords
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the history operation needs a consistent construction rule so topology identity survives native history reconstruction
def BuildHistory(
    Model: CylinderBody,
    Identity: BodyIdentity,
    TagSet: TopologyTags,
    Vertices: VertexIndices | None = None,
    Tracking: EntityIds | None = None,
) -> tuple[GeometryRecord, ...]:
    Records = list(
        AssignHeads(
            ApplyIds(
                ApplyVertices(BuildRecords(Model), Vertices or VertexIndices()),
                Tracking or EntityIds(),
            ),
            KHistoryHeads,
        )
    )
    BodyRoot = Records[1]
    Records[1] = Replace(
        BodyRoot, Fields=(BodyRoot.Fields[0], Identity.BodyKey, *BodyRoot.Fields[2:])
    )
    return (*Records, *MakeHistoryTags(Identity, TagSet))
