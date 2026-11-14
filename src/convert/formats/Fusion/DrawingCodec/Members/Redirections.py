from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RedirectDesign:
    FileVersion: int
    TargetFile: str
    DisplayName: str
    LineageUrn: str
    VersionUrn: str


@MakeDataClass(frozen=True, slots=True)
class RedirectValue:
    Name: str
    Value: str
    DataType: str


@MakeDataClass(frozen=True, slots=True)
class RedirectLink:
    Source: str
    Target: str
    Kind: str
    Properties: tuple[RedirectValue, ...]


@MakeDataClass(frozen=True, slots=True)
class Redirections:
    SchemaVersion: int
    Designs: tuple[RedirectDesign, ...]
    References: tuple[RedirectLink, ...]
