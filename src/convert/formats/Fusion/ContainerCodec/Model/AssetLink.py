from dataclasses import dataclass as MakeDataClass


# asset link needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class AssetLink:
    LinkId: str
    AssetId: str
    SnapshotId: str
    LinkWord: int
    PhysicalGuid: str
