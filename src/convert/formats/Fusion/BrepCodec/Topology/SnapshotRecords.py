from convert.formats.Fusion.BrepCodec.Attributes.SnapshotAttributes import MakeSnapTags
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.BrepCodec.Topology.ApplyVertices import ApplyVertices
from convert.formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.formats.Fusion.BrepCodec.Topology.OffsetRecord import OffsetRecord
from convert.formats.Fusion.BrepCodec.Topology.RegionGeometry import BuildCarriers
from convert.formats.Fusion.BrepCodec.Topology.RegionTopology import BuildRegion
from convert.formats.Fusion.BrepCodec.Topology.SnapshotLinks import KSnapshotHeads
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderRecords import BuildRecords
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
