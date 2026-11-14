from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


def SpanOrder(
    Entities: tuple[KJournalEntity, ...], Start: int, Finish: int, Stable: bool
) -> tuple[int, ...]:
    Roots = tuple(
        Index for Index in range(Start, Finish) if isinstance(Entities[Index], BodyNode)
    )
    Others = tuple(
        Index for Index in range(Start, Finish) if Index not in Roots and Index != 0
    )
    Flipped = list(reversed(Others))
    if Stable:
        Bearers = [
            Index for Index in Others if WalkSubtypes(EntitySubtree(Entities[Index]))
        ]
        Slots = [Position for Position, Index in enumerate(Flipped) if Index in Bearers]
        for Position, Index in zip(Slots, Bearers):
            Flipped[Position] = Index
    return ((0,) if Start == 0 else ()) + Roots + tuple(Flipped)


def ShuffleOrder(
    Entities: tuple[KJournalEntity, ...], ActiveCount: int, Stable: bool
) -> tuple[int, ...]:
    return SpanOrder(Entities, 0, ActiveCount, Stable) + SpanOrder(
        Entities, ActiveCount, len(Entities), Stable
    )
