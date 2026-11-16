from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Reading.GeometryTokens import GeometryTokens
from convert.Formats.Fusion.BrepCodec.Topology.HistoryRecords import BuildHistory
from convert.Formats.Fusion.BrepCodec.Topology.SnapshotRecords import BuildSnapshot
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the profile records contract needs a shared interpretation so topology identity survives native history reconstruction
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
