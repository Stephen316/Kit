from typing import TypedDict


# schema data needs an explicit state contract so appearance references remain connected to their owning entities
class SchemaData(TypedDict):
    TagName: str
    Attributes: list[tuple[str, str]]
    Children: list["SchemaData"]
