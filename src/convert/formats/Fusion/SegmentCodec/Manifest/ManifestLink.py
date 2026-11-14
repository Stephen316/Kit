from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ManifestLink:
    LinkId: str
    SourcePath: str
    CachePath: str
    XrefPath: str
    Properties: tuple[tuple[str, str], ...]
