from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftKey,
    KDraftState,
)

# the segment key shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KSegmentKey = tuple[KDraftKey, int]


# the state contents contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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
