from dataclasses import dataclass as MakeDataClass


# redirect reference needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class RedirectRef:
    SourceName: str
    TargetName: str
    Properties: tuple[tuple[str, str], ...]
