from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    MoveSlab,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Pattern.PatternSolid import (
    CopyPlaces,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSealed

# the body copy specification variants need one shared contract so parametric feature reconstruction cannot omit a supported value shape
KBodyCopySpec = BodyGridSpec | BodyRingSpec


# the copy layout contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def CopyLayout(Feature: KBodyCopySpec) -> PatternSpec | CircularSpec:
    if isinstance(Feature, BodyRingSpec):
        return CircularSpec(0, Feature.Count, Feature.TotalDegrees)
    return PatternSpec(
        0, Feature.CountU, Feature.SpacingUMm, Feature.CountV, Feature.SpacingVMm
    )


# copy bodies needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def CopyBodies(
    Source: PrismSolid, Feature: KBodyCopySpec, Operation: int, Ordinal: int
) -> tuple[PrismSolid, ...]:
    if IsSealed(Source):
        raise ValueError(
            "Fusion body patterns take bodies that are not tapered or swept"
        )
    Copies: list[PrismSolid] = []
    for Index, Place in enumerate(CopyPlaces(CopyLayout(Feature), 0.0)):
        Extra = (Operation, Operation + Index + 1)
        Copies.append(
            PrismSolid(
                tuple(MoveSlab(SlabValue, Place, Extra) for SlabValue in Source.Slabs),
                FaceLabel(str(Operation), (), Index + 1),
                Ordinal=Ordinal + Index,
            )
        )
    return tuple(Copies)
