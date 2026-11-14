from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DesignTarget:
    DisplayName: str
    AssetId: str
    SnapshotId: str
    ChangeGuid: str
    ComponentGuid: str
    BodyPersistentId: str
    InstanceId: int
    ComponentId: int
    BodiesId: int
    SketchesId: int
    BodyVersion: int = 1
    DesignVersion: int = 1
