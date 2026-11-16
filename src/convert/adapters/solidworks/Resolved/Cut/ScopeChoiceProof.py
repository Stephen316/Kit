from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.BossEntry import OpNode
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import SurfaceOwner
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeChoice, ScopeOwner
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey


# chooser face roles require the earlier cap and contour rather than the ordinal alone
def ScopeChoiceKeys(
    Choice: ScopeChoice, Owner: ScopeOwner, CutValue: OpNode, CutEdges: frozenset[int]
) -> set[tuple[int, int, int, int]]:
    First, Second = (Face["surfaces"] for Face in Choice["faces"])
    RequireArch(
        tuple((Item["class"], Item["occurrence"]) for Item in First),
        ((Owner.CapClass, 0), *((Owner.EdgeClass, Edge) for Edge in Owner.CapEdges)),
        "scope chooser retains earlier cap and ordered sides",
    )
    Earlier = [Item for Item in Second if Item["feature_id"] == Owner.FeatureId]
    RequireArch(
        tuple((Item["class"], Item["occurrence"]) for Item in Earlier),
        ((Owner.CapClass, 0), (Owner.CapClass, 1)),
        "scope chooser second face retains both earlier caps",
    )
    RequireArch(
        {SurfaceOwner(Item) for Item in (*First, *Earlier)},
        {Owner.SurfaceOwner},
        "scope chooser retains the earlier file and clock",
    )
    CutItems = [Item for Item in Second if Item["feature_id"] != Owner.FeatureId]
    RequireArch(
        {
            (Item["file_ref_object"], Item["feature_id"], Item["class"])
            for Item in CutItems
        },
        {
            (
                CutValue["file_ref_object"],
                CutValue["native_feature_id"],
                "moFromSktEnt3IntSurfIdRep_c",
            )
        },
        "scope chooser keeps typed sides from the reached cut",
    )
    SideIds = {Item["occurrence"] for Item in CutItems}
    RequireArch(
        len(SideIds) == 3 and SideIds <= CutEdges,
        True,
        "scope chooser sides belong to its cut contour",
    )
    RequireArch(
        len({Item["time_word"] for Item in CutItems}),
        1,
        "scope chooser cut side clocks agree",
    )
    return {SurfaceKey(Item) for Item in CutItems}
