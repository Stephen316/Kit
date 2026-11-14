from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PlaceKeys:
    Instance: int
    NodeId: int
    NodeData: int
    Feature: int
    FeatureData: int
    Status: int
    Table: int
    Occurrence: int
    Nested: tuple[int, ...]
    PersistentId: str
    InstanceId: int
    FeatureId: int
    FeatureIndex: int
    ActInstance: int
    ActData: int
    ActTable: int
    ActCopy: int
    EntryId: int
