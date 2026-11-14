from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ClassStamp:
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
