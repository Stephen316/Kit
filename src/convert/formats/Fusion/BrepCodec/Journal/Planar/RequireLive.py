from typing import TypeVar

from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable

KLiveNode = TypeVar("KLiveNode")


def RequireLive(
    Table: LiveTable, Reference: int, ClassType: type[KLiveNode]
) -> KLiveNode:
    if not 0 <= Reference < len(Table.Entities):
        raise ValueError("Missing Fusion planar topology reference")
    Value = Table.Entities[Reference]
    if not isinstance(Value, ClassType):
        raise ValueError("Unsupported Fusion planar topology target")
    return Value
