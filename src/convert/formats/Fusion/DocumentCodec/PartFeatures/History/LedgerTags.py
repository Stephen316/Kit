from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody


def LedgerTags(
    Bodies: tuple[ShapeBody, ...], Ledger: TagLedger
) -> list[tuple[dict[tuple[object, ...], int], int]]:
    BodyTags = [Ledger.Claim(("body", BodyValue.Ordinal)) for BodyValue in Bodies]
    return [
        (Ledger.FaceTags(BodyValue, BodyValue.Ordinal), BodyTag)
        for BodyValue, BodyTag in zip(Bodies, BodyTags, strict=True)
    ]
