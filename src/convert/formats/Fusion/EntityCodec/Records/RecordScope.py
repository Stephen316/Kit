from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RecordScope:
    ClassCodes: Mapping[int, str]
    Continuations: Mapping[int, frozenset[str]]
