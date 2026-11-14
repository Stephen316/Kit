from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AssetLink:
    LinkId: str
    AssetId: str
    SnapshotId: str
    LinkWord: int
    PhysicalGuid: str
