from typing import TypedDict


class SchemaData(TypedDict):
    TagName: str
    Attributes: list[tuple[str, str]]
    Children: list["SchemaData"]
