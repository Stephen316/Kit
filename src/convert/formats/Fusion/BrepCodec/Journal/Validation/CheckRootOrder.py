from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


def CheckRootOrder(
    Entities: tuple[KJournalEntity, ...], Order: tuple[int, ...]
) -> None:
    Original = tuple(
        Index for Index, Value in enumerate(Entities) if isinstance(Value, BodyNode)
    )
    Reordered = tuple(Index for Index in Order if isinstance(Entities[Index], BodyNode))
    if Original != Reordered:
        raise ValueError("Fusion allocation must preserve serialized body-root order")
