from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyCollection import ReadBodyList, ReadBodyOwner
from convert.formats.Fusion.Topology.ResultBody import IndexBodyLinks
from interchange.features.FeatureStep import FeatureStep


# an explicit body inventory prevents partial modeling history from posing as a final shape
def ReadRevBodies(
    BulkData: bytes, Owners: dict[int, RecordSpan], Steps: tuple[FeatureStep, ...]
) -> tuple[dict[str, tuple[int, int]], int, int]:
    FeatureIds = {
        StepValue.id: int(StepValue.provenance.native_id)
        for StepValue in Steps
        if StepValue.provenance is not None
    }
    if len(FeatureIds) != len(Steps) or len(set(FeatureIds.values())) != len(Steps):
        raise ValueError("Missing or duplicate Fusion Revolve creator identities")
    Links = IndexBodyLinks(BulkData, Owners, frozenset(FeatureIds.values()))
    BodyIds = frozenset(BodyId for BodyId, _ in Links.values())
    if len(BodyIds) != len(Links):
        raise ValueError("Fusion Revolve creators share a result body")
    CollectionIds = {ReadBodyOwner(BulkData, Owners, BodyId) for BodyId in BodyIds}
    if len(CollectionIds) != 1:
        raise ValueError("Fusion Revolve results do not share one component collection")
    (CollectionId,) = CollectionIds
    Members, ComponentId = ReadBodyList(BulkData, Owners, CollectionId)
    if frozenset(Members) != BodyIds:
        raise ValueError(
            "Fusion Revolve creators do not cover the native body collection"
        )
    return (
        {StepId: Links[FeatureId] for StepId, FeatureId in FeatureIds.items()},
        CollectionId,
        ComponentId,
    )
