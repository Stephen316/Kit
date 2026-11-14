from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ClassRow:
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    ClassSpace: str
