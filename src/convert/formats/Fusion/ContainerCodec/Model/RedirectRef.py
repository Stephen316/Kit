from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RedirectRef:
    SourceName: str
    TargetName: str
    Properties: tuple[tuple[str, str], ...]
