from dataclasses import dataclass as MakeDataClass


# object reference needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class ObjectRef:
    ClassName: str
    ObjectId: str
