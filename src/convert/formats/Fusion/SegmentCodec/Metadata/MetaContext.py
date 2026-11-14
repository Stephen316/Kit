from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class MetaContext:
    Token: int
    LinkId: str
    RevisionId: str
    VersionUrn: str
    AssetId: str
    SegmentId: int
