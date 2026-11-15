from dataclasses import dataclass as MakeDataClass


# field rule needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class FieldRule:
    FieldName: str
    WireKind: str
    ItemCount: int = 1
