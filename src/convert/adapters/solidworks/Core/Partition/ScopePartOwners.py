from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import (
    ScopeBody,
    ScopedCut,
    ScopeOwner,
)


# affected body identities come from the active scope list rather than result choosers
def GetScopeBodies(CutValue: ScopedCut) -> tuple[ScopeBody, ...]:
    Primary, Later = CutValue["primary_bodies"], CutValue["later_bodies"]
    IsExplicit = CutValue["scope_kind"] == "explicit"
    RequireArch(
        (
            CutValue["scope_kind"],
            CutValue["scope_word"],
            Primary["present"],
            Later["present"],
        ),
        ("explicit", 1, True, False) if IsExplicit else ("all_bodies", 0, False, True),
        "typed cut scope list route",
    )
    Active, Inactive = (Primary, Later) if IsExplicit else (Later, Primary)
    RequireArch(Inactive["bodies"], (), "empty inactive cut scope list")
    Bodies = Active["bodies"]
    RequireArch(
        len(Bodies) in ((1, 2) if IsExplicit else (2,)),
        True,
        "bounded affected body roster",
    )
    RequireArch(
        CutValue["scope_body_ids"],
        tuple(BodyValue["body_id"] for BodyValue in Bodies) if IsExplicit else (),
        "authored scope selection agrees with the primary list",
    )
    RequireArch(
        tuple(BodyValue["recent_atom_id"] for BodyValue in Bodies),
        CutValue["atom_ids"][: len(Bodies)],
        "affected scope list agrees with cut result atoms",
    )
    return Bodies


# an excluded body carries forward the original atom established by its earlier boss
def BindScopeAtoms(
    CutValue: ScopedCut, Owners: tuple[ScopeOwner, ScopeOwner]
) -> dict[int, tuple[int, ScopeBody | None]]:
    BodyOwners = {Owner.BodyId: Owner for Owner in Owners}
    CutId = CutValue["native_feature_id"]
    RequireArch(
        len(BodyOwners) == len({Owner.FeatureId for Owner in Owners}) == 2
        and CutId > 0
        and all(
            Owner.BodyId > 0 and Owner.FeatureId > 0 and Owner.FeatureId != CutId
            for Owner in Owners
        ),
        True,
        "two distinct original body and earlier feature identities",
    )
    RequireArch(
        {Owner.FileObject for Owner in Owners},
        {CutValue["file_ref_object"]},
        "cut and original body owners share an archive",
    )
    Result: dict[int, tuple[int, ScopeBody | None]] = {
        Owner.BodyId: (Owner.BodyId, None) for Owner in Owners
    }
    Bodies = GetScopeBodies(CutValue)
    RequireArch(
        len({BodyValue["body_id"] for BodyValue in Bodies}),
        len(Bodies),
        "distinct affected body IDs",
    )
    for BodyValue in Bodies:
        Owner = BodyOwners.get(BodyValue["body_id"])
        RequireArch(
            Owner is not None
            and BodyValue["feature_id"] == Owner.FeatureId
            and 0 <= BodyValue["offset"] < BodyValue["end"] <= CutValue["stream_end"],
            True,
            "cut body resolves to its original owner and record span",
        )
        Result[BodyValue["body_id"]] = (BodyValue["recent_atom_id"], BodyValue)
    RequireArch(
        len({AtomId for AtomId, _ in Result.values()}),
        2,
        "distinct atoms for both projected bodies",
    )
    return Result
