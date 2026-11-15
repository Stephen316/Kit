from dataclasses import dataclass as MakeDataClass


# meta context needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class MetaContext:
    Token: int
    LinkId: str
    RevisionId: str
    VersionUrn: str
    AssetId: str
    SegmentId: int
