from collections.abc import Callable
from dataclasses import dataclass as Dataclass
from typing import TypeVar

from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor

# different inline geometry records need to retain the same positioned read contract
KMemberValue = TypeVar("KMemberValue")


# exact typed boundaries distinguish saved member provenance from nearby marker offsets
@Dataclass(frozen=True, slots=True)
class MemberSpan:
    Offset: int
    EndOffset: int


# a dimension body keeps the activity and scalar location needed by its neutral relation
@Dataclass(frozen=True, slots=True)
class DistanceSpan:
    Body: MemberSpan
    ScalarOffset: int
    TypeCode: int
    ActivePair: bool


# sketch member slots preserve their own record boundaries when decoded together
@Dataclass(frozen=True, slots=True)
class MemberSpans:
    Points: tuple[MemberSpan, ...]
    Lines: tuple[MemberSpan, ...]
    Distances: tuple[DistanceSpan, ...]


# source spans must include the framed member type and all its owned fields
def ReadMemberRows(
    Cursor: ArchiveCursor, Count: int, ReadMember: Callable[[], KMemberValue]
) -> tuple[list[KMemberValue], tuple[MemberSpan, ...]]:
    Values: list[KMemberValue] = []
    Spans: list[MemberSpan] = []
    for _ in range(Count):
        Offset = Cursor.Offset
        Values.append(ReadMember())
        Spans.append(MemberSpan(Offset, Cursor.Offset))
    return Values, tuple(Spans)
