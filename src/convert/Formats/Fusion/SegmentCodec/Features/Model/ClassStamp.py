from dataclasses import dataclass as MakeDataClass


# class stamp needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class ClassStamp:
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
