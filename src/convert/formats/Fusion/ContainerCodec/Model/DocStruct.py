from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DocStruct:
    Version: str
    TypeName: str
    Subtype: str
    Attributes: tuple[tuple[str, bool], ...]
