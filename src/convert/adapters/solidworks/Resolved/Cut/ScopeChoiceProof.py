from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.BossEntry import OpNode
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import SurfaceOwner
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeChoice, ScopeOwner
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey


# chooser face roles require the earlier cap and contour rather than the ordinal alone
def ScopeChoiceKeys(
    Choice: ScopeChoice, Owner: ScopeOwner, CutValue: OpNode, CutEdges: frozenset[int]
) -> set[tuple[int, int, int, int]]:
    First, Second = (FaceInfo["surfaces"] for FaceInfo in Choice["faces"])
    RequireArch(
        tuple((Surface["class"], Surface["occurrence"]) for Surface in First),
        (
            (Owner.CapClass, 0),
            *((Owner.EdgeClass, EdgeId) for EdgeId in Owner.CapEdges),
        ),
        "scope chooser retains earlier cap and ordered sides",
    )
    Earlier = [
        Surface for Surface in Second if Surface["feature_id"] == Owner.FeatureId
    ]
    RequireArch(
        tuple((Surface["class"], Surface["occurrence"]) for Surface in Earlier),
        ((Owner.CapClass, 0), (Owner.CapClass, 1)),
        "scope chooser second face retains both earlier caps",
    )
    RequireArch(
        {SurfaceOwner(Surface) for Surface in (*First, *Earlier)},
        {Owner.SurfaceOwner},
        "scope chooser retains the earlier file and clock",
    )
    CutItems = [
        Surface for Surface in Second if Surface["feature_id"] != Owner.FeatureId
    ]
    RequireArch(
        {
            (Surface["file_ref_object"], Surface["feature_id"], Surface["class"])
            for Surface in CutItems
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
    SideIds = {Surface["occurrence"] for Surface in CutItems}
    RequireArch(
        len(SideIds) == 3 and SideIds <= CutEdges,
        True,
        "scope chooser sides belong to its cut contour",
    )
    RequireArch(
        len({Surface["time_word"] for Surface in CutItems}),
        1,
        "scope chooser cut side clocks agree",
    )
    return {SurfaceKey(Surface) for Surface in CutItems}
