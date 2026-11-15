from dataclasses import dataclass as MakeDataClass


# manifest link needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class ManifestLink:
    LinkId: str
    SourcePath: str
    CachePath: str
    XrefPath: str
    Properties: tuple[tuple[str, str], ...]
