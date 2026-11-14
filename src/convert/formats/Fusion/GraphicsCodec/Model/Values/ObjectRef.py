from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ObjectRef:
    ClassName: str
    ObjectId: str
