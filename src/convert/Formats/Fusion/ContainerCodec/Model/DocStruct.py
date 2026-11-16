from dataclasses import dataclass as MakeDataClass


# doc struct needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DocStruct:
    Version: str
    TypeName: str
    Subtype: str
    Attributes: tuple[tuple[str, bool], ...]
