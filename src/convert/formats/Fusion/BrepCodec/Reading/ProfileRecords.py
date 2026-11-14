from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Reading.GeometryTokens import GeometryTokens
from convert.formats.Fusion.BrepCodec.Topology.HistoryRecords import BuildHistory
from convert.formats.Fusion.BrepCodec.Topology.SnapshotRecords import BuildSnapshot
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ProfileRecords(HasHistory: bool) -> tuple[AsmRecord, ...]:
    Model = CylinderBody(1.0, 1.0, (0.0, 0.0, 0.0))
    Label = FeatureTag("1", (0,))
    TagSet = TopologyTags(Label, Label, Label, Label, Label, SketchLink(0, 0, 0, 1, 1))
    Records = (
        BuildHistory(Model, BodyIdentity(0, 0, 0, 0), TagSet)
        if HasHistory
        else BuildSnapshot(Model, TagSet)
    )
    return GeometryTokens(Records)
