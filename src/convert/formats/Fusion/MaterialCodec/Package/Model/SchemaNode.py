from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SchemaNode:
    TagName: str
    Attributes: tuple[tuple[str, str], ...]
    Children: tuple["SchemaNode", ...]
    TextValue: str = ""
