from convert.Formats.Fusion.BrepCodec.Attributes.SnapshotAttributes import MakeSnapTags
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.BrepCodec.Topology.ApplyVertices import ApplyVertices
from convert.Formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.Formats.Fusion.BrepCodec.Topology.OffsetRecord import OffsetRecord
from convert.Formats.Fusion.BrepCodec.Topology.RegionGeometry import BuildCarriers
from convert.Formats.Fusion.BrepCodec.Topology.RegionTopology import BuildRegion
from convert.Formats.Fusion.BrepCodec.Topology.SnapshotLinks import KSnapshotHeads
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderRecords import BuildRecords
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the snapshot operation needs a consistent construction rule so topology identity survives native history reconstruction
def BuildSnapshot(
    Model: CylinderBody, TagSet: TopologyTags, Vertices: VertexIndices | None = None
) -> tuple[GeometryRecord, ...]:
    CylinderRows = ApplyVertices(BuildRecords(Model), Vertices or VertexIndices())
    Roots = (
        CylinderRows[0],
        OffsetRecord(CylinderRows[1]),
        MakeRecord("body", (EntityRef(28), EntityRef(-1), EntityRef(-1))),
        MakeRecord("body", (EntityRef(38), EntityRef(-1), EntityRef(-1))),
    )
    Owned = tuple(OffsetRecord(Record) for Record in CylinderRows[2:])
    DoubleRegion = (*BuildRegion(2, 28, True), *BuildCarriers(Model))
    SingleRegion = (*BuildRegion(3, 38, False), *BuildCarriers(Model))
    Topology = (*Roots, *Owned, *DoubleRegion, *SingleRegion)
    return (*AssignHeads(Topology, KSnapshotHeads), *MakeSnapTags(TagSet))
