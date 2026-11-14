from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy


def BlockSolid(
    WidthCm: float, DepthCm: float, HeightCm: float, Policy: AuthorPolicy
) -> PrismSolid:
    Operation = (Policy.FirstOperationId + 1,)
    Corners = ((0.0, 0.0), (WidthCm, 0.0), (WidthCm, DepthCm), (0.0, DepthCm))
    Names = tuple(
        str(Policy.CurveProgenitorTag + (Index + 1) % 4) for Index in range(4)
    )
    LoopValue = tuple(
        LineSpan(
            Corners[Index], Corners[(Index + 1) % 4], FaceLabel(Names[Index], Operation)
        )
        for Index in range(4)
    )
    SlabValue = PrismSlab(
        0.0,
        HeightCm,
        (CanonLoop(LoopValue),),
        FaceLabel(Policy.BottomFaceLabel, Operation),
        FaceLabel(Policy.TopFaceLabel, Operation),
    )
    BodyLabel = FaceLabel(str(Operation[0]), (), Policy.CurveProgenitorTag + 4)
    Curves = tuple(
        (LoopValue[Index].Label, Policy.FirstSketchTag + 5 + Index)
        for Index in range(4)
    )
    return PrismSolid((SlabValue,), BodyLabel, Curves)
