from dataclasses import dataclass as MakeDataClass


# schema node needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class SchemaNode:
    TagName: str
    Attributes: tuple[tuple[str, str], ...]
    Children: tuple["SchemaNode", ...]
    TextValue: str = ""
