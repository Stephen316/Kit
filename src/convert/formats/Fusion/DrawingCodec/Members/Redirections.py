from dataclasses import dataclass as MakeDataClass


# redirect design needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class RedirectDesign:
    FileVersion: int
    TargetFile: str
    DisplayName: str
    LineageUrn: str
    VersionUrn: str


# redirect value needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class RedirectValue:
    Name: str
    Value: str
    DataType: str


# redirect link needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class RedirectLink:
    Source: str
    Target: str
    Kind: str
    Properties: tuple[RedirectValue, ...]


# redirections needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class Redirections:
    SchemaVersion: int
    Designs: tuple[RedirectDesign, ...]
    References: tuple[RedirectLink, ...]
