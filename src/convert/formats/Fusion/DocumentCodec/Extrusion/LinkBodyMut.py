from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Extrusion.BodyCache import BodyCache
from convert.formats.Fusion.DocumentCodec.Extrusion.LinkBodyTags import LinkBodyTags


def LinkBodyMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "body",
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles["body"]),
        cache=BodyCache(Author),
        massProperties=Author.MakeValue("MassPropertiesValue"),
        persistentId=Author.BodyId,
        physicalMaterial=Author.MakeValue("PhysicalMaterialValue"),
        rGroupParent=Reference("bodies"),
        userName=Author.SpecValue.BodyName,
        visualMaterial=Author.MakeValue("VisualMaterialValue"),
    )
    Author.Change("bodies_root", rootId="BodiesRoot", rooted=[Reference("body")])
    Author.Change(
        "bodies",
        creationIndex=1,
        groupChildren=[Reference("body")],
        passiveIdGenerator=Reference("body_passive_ids"),
    )
    Author.Change("body_passive_ids", rBodies=Reference("bodies"))
    Author.Change(
        "brep_history",
        mapBodyId=[{"key": Author.Policy.BodyKey, "value": Author.Roles["body"]}],
        partName=Author.BrepPart,
    )
    Author.Change(
        "dc_body",
        bodyUuid=Author.BodyId,
        rBody=Reference("body"),
        rOwnFeature=Reference("dc_extrude"),
    )
    LinkBodyTags(Author)
