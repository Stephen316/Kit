from convert.formats.Fusion.DocumentCodec.Materials.PhysicalValue import PhysicalValue
from convert.formats.Fusion.DocumentCodec.Materials.VisualValue import VisualValue
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import BodyRole
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartCache import PartCache
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage


def LinkBodiesMut(
    Author: AuthorState, Final: PartStage, BodyTags: dict[int, int]
) -> None:
    Reference = Author.Reference
    Ordinals = [Solid.Ordinal for Solid in Final.Bodies]
    Shown = [Reference(BodyRole(Ordinal, "body")) for Ordinal in Final.Shown]
    Author.Change(
        "bodies", creationIndex=len(Ordinals), groupChildren=Shown, children=Shown
    )
    Rooted = [
        RoleName
        for Ordinal in Ordinals
        for RoleName in (BodyRole(Ordinal, "pm_body"), BodyRole(Ordinal, "body"))
        if RoleName in Author.Roles
    ]
    Author.Change(
        "bodies_root",
        rootId="BodiesRoot",
        rooted=[Reference(RoleName) for RoleName in Rooted],
    )
    Author.Change(
        "brep_history",
        mapBodyId=[
            {"key": BodyTags[Ordinal], "value": Author.Roles[BodyRole(Ordinal, "body")]}
            for Ordinal in Ordinals
        ],
        partName=Author.BrepPart,
    )
    Author.Change(
        "fragment",
        dcBodies=[Reference(BodyRole(Ordinal, "dc_body")) for Ordinal in Ordinals],
    )
    for Solid in Final.Bodies:
        BodyName = BodyRole(Solid.Ordinal, "body")
        IsShown = Solid.Ordinal in Final.Shown
        Author.Change(
            BodyName,
            cache=PartCache(Author, Solid),
            isVisible=IsShown,
            physicalMaterial=PhysicalValue(Author),
            visualMaterial=VisualValue(Author),
        )
        Author.Change(BodyRole(Solid.Ordinal, "dc_body"), isEliminated=not IsShown)
        if BodyRole(Solid.Ordinal, "pm_body") in Author.Roles:
            Author.Change(
                BodyRole(Solid.Ordinal, "pm_body"),
                physicalMaterial=PhysicalValue(Author),
                visualMaterial=VisualValue(Author),
            )
