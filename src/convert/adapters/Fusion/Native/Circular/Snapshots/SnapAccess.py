from typing import TypeVar

from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)

KEntityType = TypeVar("KEntityType")


def SnapEntity(
    State: GeometryState, Identity: int, ClassType: type[KEntityType]
) -> KEntityType:
    if not 0 <= Identity < len(State.Entities) or not isinstance(
        State.Entities[Identity], ClassType
    ):
        raise ValueError(
            "Native circular snapshot has an incompatible topology reference"
        )
    Result = State.Entities[Identity]
    if not isinstance(Result, ClassType):
        raise ValueError("Native circular snapshot entity type changed")
    return Result
