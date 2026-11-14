from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    ProfileLoop,
)


def ToolLabels(Feature: ExtrudeSpec, Operation: int) -> tuple[FaceLabel, ...]:
    IsTwoSided = Feature.Extent in ("symmetric", "two")
    return tuple(
        FaceLabel(
            str(Index + 3),
            (Operation,),
            0,
            (FaceLabel(str(Index + 3), (Operation + 1,)),) if IsTwoSided else (),
        )
        for Index in range(len(Feature.Profile))
    )


def ToolRange(Feature: ExtrudeSpec) -> tuple[float, float]:
    Distance = Feature.DistanceMm / 10.0
    if Feature.Extent == "flip":
        return (-Distance, 0.0)
    if Feature.Extent == "symmetric":
        return (-Distance / 2.0, Distance / 2.0)
    if Feature.Extent == "two":
        return (-Feature.AgainstMm / 10.0, Distance)
    return (0.0, Distance)


def ToolSlab(Feature: ExtrudeSpec, Operation: int) -> PrismSlab:
    Lower, Upper = ToolRange(Feature)
    Start, Finish = FaceLabel("1", (Operation,)), FaceLabel("2", (Operation,))
    Floor, Ceiling = (Finish, Start) if Feature.Extent == "flip" else (Start, Finish)
    LoopValue = ProfileLoop(Feature.Profile, ToolLabels(Feature, Operation))
    return PrismSlab(Lower, Upper, (LoopValue,), Floor, Ceiling)


def ToolEdgeTags(
    Feature: ExtrudeSpec, Operation: int, CurveTag: int
) -> tuple[tuple[FaceLabel, float, FaceLabel], ...]:
    if len(Feature.Profile) != 1 or not isinstance(Feature.Profile[0], CircleCurve):
        return ()
    Lower, Upper = ToolRange(Feature)
    Start, Finish = (Upper, Lower) if Feature.Extent == "flip" else (Lower, Upper)
    WallLabel = ToolLabels(Feature, Operation)[0]
    return (
        (WallLabel, Start, FaceLabel("-" + str(CurveTag), (Operation,), 0)),
        (WallLabel, Finish, FaceLabel("-1", (Operation,), 0)),
    )
