from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass


# record scope needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class RecordScope:
    ClassCodes: Mapping[int, str]
    Continuations: Mapping[int, frozenset[str]]
