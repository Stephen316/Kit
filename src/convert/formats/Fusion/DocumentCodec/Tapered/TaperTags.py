from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy


def TaperTags(Policy: AuthorPolicy) -> TopologyTags:
    Operations = (Policy.FirstOperationId + 1,)
    SketchId = Policy.FirstSketchTag + 2
    return TopologyTags(
        FeatureTag(Policy.SideFaceLabel, Operations),
        FeatureTag(Policy.TopFaceLabel, Operations),
        FeatureTag(Policy.BottomFaceLabel, Operations),
        FeatureTag(Policy.TopEdgeLabel, Operations),
        FeatureTag("-" + str(SketchId), Operations),
        SketchLink(SketchId, 0, 0, 1, 1),
    )
