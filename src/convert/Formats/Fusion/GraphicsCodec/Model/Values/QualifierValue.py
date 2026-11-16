from dataclasses import dataclass as MakeDataClass


# qualifier value needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class QualifierValue:
    ImagePath: str | None
