from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    MoveSlab,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PatternSolid import (
    CopyPlaces,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSealed

KBodyCopySpec = BodyGridSpec | BodyRingSpec


def CopyLayout(Feature: KBodyCopySpec) -> PatternSpec | CircularSpec:
    if isinstance(Feature, BodyRingSpec):
        return CircularSpec(0, Feature.Count, Feature.TotalDegrees)
    return PatternSpec(
        0, Feature.CountU, Feature.SpacingUMm, Feature.CountV, Feature.SpacingVMm
    )


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
