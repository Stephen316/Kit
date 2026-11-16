from dataclasses import dataclass as MakeDataClass


# draft entity needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(slots=True)
class DraftEntity:
    RoleName: str
    ClassName: str
    ParentRole: str | None
    RootName: str
    FieldValues: dict[str, object]
    NamedPairs: list[dict[str, object]] | None
    Subjects: list[str]
