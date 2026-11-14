from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftKey,
    KDraftState,
)

KSegmentKey = tuple[KDraftKey, int]


def StateContents(
    States: tuple[KDraftState, ...],
) -> list[dict[KSegmentKey, tuple[object, ...]]]:
    Segments: dict[KDraftKey, int] = {}
    Present: set[KDraftKey] = set()
    Result: list[dict[KSegmentKey, tuple[object, ...]]] = []
    for State in States:
        KeyList = [KeyValue for KeyValue, _ in State]
        Current = set(KeyList)
        for KeyValue in Current - Present:
            Segments[KeyValue] = Segments.get(KeyValue, -1) + 1
        Present = Current
        Contents: dict[KSegmentKey, tuple[object, ...]] = {}
        for KeyValue, NodeValue in State:
            Record = MakeEntityNode(NodeValue)
            Tokens = tuple(
                (
                    TagValue,
                    (
                        (KeyList[Value], Segments[KeyList[Value]])
                        if TagValue == 12 and isinstance(Value, int) and Value >= 0
                        else Value
                    ),
                )
                for TagValue, Value in Record.Tokens
            )
            Contents[(KeyValue, Segments[KeyValue])] = (Record.Name, Tokens)
        Result.append(Contents)
    return Result
