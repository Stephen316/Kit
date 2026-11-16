from dataclasses import dataclass as MakeDataClass


# class row needs an explicit state contract so sheet objects retain their intended document relationships
@MakeDataClass(frozen=True, slots=True)
class ClassRow:
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    ClassSpace: str
