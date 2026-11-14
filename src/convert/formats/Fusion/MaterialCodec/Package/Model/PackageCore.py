from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PackageCore:
    Identifier: str
    Created: str
    Updated: str
    Updates: int
    NameValue: str | None = None
    EmbedOption: int | None = None
    LastSaved: str | None = None
    IsReadOnly: bool | None = None
