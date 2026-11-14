from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy


def CuboidTags(Policy: AuthorPolicy) -> PrismTags:
    FirstTag = Policy.CurveProgenitorTag
    Operations = (Policy.FirstOperationId + 1,)
    Names = (
        Policy.BottomFaceLabel,
        Policy.TopFaceLabel,
        str(FirstTag + 1),
        str(FirstTag + 3),
        str(FirstTag),
        str(FirstTag + 2),
    )
    return PrismTags(
        tuple(FeatureTag(Label, Operations) for Label in Names),
        tuple(
            SketchLink(Policy.FirstSketchTag + Index + 5, 0, 0, 1, 1)
            for Index in range(4)
        ),
    )
