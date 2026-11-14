from dataclasses import dataclass as MakeDataClass


@MakeDataClass(slots=True)
class DraftEntity:
    RoleName: str
    ClassName: str
    ParentRole: str | None
    RootName: str
    FieldValues: dict[str, object]
    NamedPairs: list[dict[str, object]] | None
    Subjects: list[str]
