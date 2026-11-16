from dataclasses import dataclass as MakeDataClass


# root link needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class RootLink:
    Role: str
    Unresolved: str | None
    SourcePath: str
    TargetPath: str
    LocalPath: str
    Words: tuple[int, int, int, int]
    Properties: tuple[tuple[str, str], ...]
