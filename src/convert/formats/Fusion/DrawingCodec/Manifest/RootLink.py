from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RootLink:
    Role: str
    Unresolved: str | None
    SourcePath: str
    TargetPath: str
    LocalPath: str
    Words: tuple[int, int, int, int]
    Properties: tuple[tuple[str, str], ...]
