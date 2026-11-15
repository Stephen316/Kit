from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.DocumentCodec.Form.FormCache import FormCache
from convert.formats.Fusion.DocumentCodec.Form.FormParts import FormParts
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Materials.PhysicalValue import PhysicalValue
from convert.formats.Fusion.DocumentCodec.Materials.VisualValue import VisualValue
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def IsClosedForm(Model: FormBody) -> bool:
    UseCount = sum(len(FaceValue.Uses) for FaceValue in Model.Faces)
    return UseCount == 2 * len(Model.Edges)


def LinkFormBodyMut(Author: AuthorState, SpecValue: FormSpec, Parts: FormParts) -> None:
    Reference = Author.Reference
    Author.Change(
        "body",
        actIdentifier=f"{Author.Policy.DesignSegmentId}_{Author.Roles['body']}",
        bodyType=2 if IsClosedForm(SpecValue.Body) else 4,
        cache=FormCache(Author, SpecValue.Body, IsClosedForm(SpecValue.Body)),
        massProperties=Author.MakeValue("MassPropertiesValue"),
        persistentId=Author.BodyId,
        rGroupParent=Reference("bodies"),
        userName=SpecValue.BodyName,
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
        "cache_bodies", creationIndex=1, groupChildren=[Reference("form_node")]
    )
    Author.Change("cache_serializer", partName=Parts.Snapshot)
    Author.Change(
        "dc_body",
        bodyUuid=Author.BodyId,
        rBody=Reference("body"),
        rOwnFeature=Reference("form_feature"),
    )


def LinkNodeMatMut(Author: AuthorState) -> None:
    Author.Change(
        "form_node",
        physicalMaterial=PhysicalValue(Author),
        visualMaterial=VisualValue(Author),
    )
    Author.Change(
        "protein", PhysicalMaterialRefCountVector=[2], VisualMaterialRefCountVector=[2]
    )
