from dataclasses import dataclass as MakeDataClass


# redirect design needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class RedirectDesign:
    FileVersion: int
    TargetName: str
    DisplayName: str
    LineageUrn: str
    VersionUrn: str
