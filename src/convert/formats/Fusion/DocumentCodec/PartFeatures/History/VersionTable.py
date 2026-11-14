from convert.formats.Fusion.DocumentCodec.PartFeatures.History.StateLedger import (
    KSegmentKey,
)


def VersionTable(
    Contents: list[dict[KSegmentKey, tuple[object, ...]]],
) -> tuple[dict[tuple[KSegmentKey, int], int], int, list[tuple[KSegmentKey, int]]]:
    Final = list(Contents[-1])
    Starts: dict[KSegmentKey, list[int]] = {}
    for Index, State in enumerate(Contents):
        for KeyValue, Content in State.items():
            Earlier = Contents[Index - 1].get(KeyValue) if Index else None
            if Earlier != Content:
                Starts.setdefault(KeyValue, []).append(Index)
    Positions: dict[tuple[KSegmentKey, int], int] = {
        (KeyValue, Starts[KeyValue][-1]): Index for Index, KeyValue in enumerate(Final)
    }
    Archived = [
        (KeyValue, Start)
        for KeyValue, Values in Starts.items()
        for Start in Values
        if (KeyValue, Start) not in Positions
    ]
    Archived.sort(key=lambda PairValue: PairValue[1])
    for Offset, PairValue in enumerate(Archived):
        Positions[PairValue] = len(Final) + Offset
    Order = [(KeyValue, Starts[KeyValue][-1]) for KeyValue in Final] + Archived
    return Positions, len(Final), Order


def VersionAt(
    Positions: dict[tuple[KSegmentKey, int], int], KeyValue: KSegmentKey, State: int
) -> int:
    return max(
        (
            Start
            for ItemValue, Start in Positions
            if ItemValue == KeyValue and Start <= State
        ),
        default=-1,
    )
