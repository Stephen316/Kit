from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RootFacts:
    Component: int
    Instances: int
    Overrides: int
    Constraints: int
    ConstraintOccs: int
    Fragment: int
    NodesId: int
    FeatureIds: int
    CreationOrder: int
    InstancesRoot: int
    ContextId: int
    RootOccurrence: int
    AssetId: str
    PersistentId: str
    ActComponent: int
    ActTable: int
    ActInstances: int
    ActRoot: int
    BrowserRoot: int
    RootEntry: int
    DesignSegment: int
    ActSegment: int
    SeedId: int
    InstanceSeed: int
