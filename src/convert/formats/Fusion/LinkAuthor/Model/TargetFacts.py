from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class TargetFacts:
    AssetId: str
    SnapshotId: str
    RevisionGuid: str
    ChangeRevs: tuple[tuple[str, str], ...]
    ActComponent: int
    ActIdentifier: str
    ActRevs: tuple[tuple[str, str], ...]
    Component: int
    Instances: int
    Features: int
    PersistentId: str
    ComponentRev: str
    DesignSegment: int
    ActSegment: int
    Children: tuple[tuple[int, tuple[float, ...]], ...]
    Slots: tuple[int, int, int]
