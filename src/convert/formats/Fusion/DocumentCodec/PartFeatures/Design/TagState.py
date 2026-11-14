from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.History.LedgerTags import (
    LedgerTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)

KFaceTags = dict[tuple[object, ...], int]


@MakeDataClass(frozen=True, slots=True)
class TagState:
    Focus: PrismSolid
    Bodies: tuple[PrismSolid, ...]


def ReplayFocus(
    States: tuple[TagState, ...], Index: int
) -> tuple[ShapeBody, KFaceTags, int, TagLedger]:
    Ledger = TagLedger()
    Found: tuple[ShapeBody, KFaceTags, int] | None = None
    for Position, StateValue in enumerate(States[: Index + 1]):
        Ordered = sorted(StateValue.Bodies, key=lambda Solid: Solid.Ordinal)
        Shapes = tuple(BuildShape(Solid) for Solid in Ordered)
        Pairs = LedgerTags(Shapes, Ledger)
        if Position != Index:
            continue
        for Shape, (FaceTags, BodyTag) in zip(Shapes, Pairs, strict=True):
            if Shape.Ordinal == StateValue.Focus.Ordinal:
                Found = (Shape, FaceTags, BodyTag)
    if Found is None:
        raise ValueError("Fusion part feature body is missing from its state")
    return Found[0], Found[1], Found[2], Ledger


def BodyTags(States: tuple[tuple[PrismSolid, ...], ...]) -> dict[int, int]:
    Ledger = TagLedger()
    Result: dict[int, int] = {}
    for Bodies in States:
        Ordered = sorted(Bodies, key=lambda Solid: Solid.Ordinal)
        Shapes = tuple(BuildShape(Solid) for Solid in Ordered)
        for Shape, (_, BodyTag) in zip(Shapes, LedgerTags(Shapes, Ledger), strict=True):
            Result[Shape.Ordinal] = BodyTag
    return Result
