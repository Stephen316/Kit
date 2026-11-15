from dataclasses import dataclass as MakeDataClass


# the keys operation needs an explicit state contract so cross document references retain their intended ownership
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
