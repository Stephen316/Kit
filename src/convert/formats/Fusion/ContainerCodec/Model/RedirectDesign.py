from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RedirectDesign:
    FileVersion: int
    TargetName: str
    DisplayName: str
    LineageUrn: str
    VersionUrn: str
