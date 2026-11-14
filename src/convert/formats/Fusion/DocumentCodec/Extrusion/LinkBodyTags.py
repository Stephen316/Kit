from convert.formats.Fusion.DocumentCodec.Extrusion.ProfileSides import ProfileSides
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def LinkBodyTags(Author: AuthorState) -> None:
    Sides = ProfileSides(Author)
    Labels = tuple(str(SideValue.ProgenitorTag) for SideValue in Sides)
    if Author.SpecValue.ProfileKind != "cuboid":
        Labels = (Author.Policy.SideFaceLabel,)
    Encoded = tuple(Label.encode("ascii") for Label in Labels)
    Offsets = [0]
    for Label in Encoded:
        Offsets.append(Offsets[-1] + len(Label))
    InfoValue = [
        Author.MakeGroup(
            "FeatureTagInfoValue",
            dict(
                facePrimIdData=list(b"".join(Encoded)),
                facePrimIdOffsets=Offsets,
                operationId=Author.Policy.FirstOperationId + 1,
                primary=False,
            ),
        )
    ]
    BodyTag = max(SideValue.ProgenitorTag for SideValue in Sides) + 1
    Author.Change(
        "body_progenitor",
        bodyUuid=Author.BodyId,
        featureTagOccMap=[
            {"key": InfoValue, "value": Author.Policy.BodyOccurrenceCount}
        ],
    )
    Author.Change(
        "extrude_progenitors",
        ProgenitorTagVec=[
            {
                "first": Author.Reference(SideValue.ProgenitorRole),
                "second": SideValue.ProgenitorTag,
            }
            for SideValue in Sides
        ]
        + [{"first": Author.Reference("body_progenitor"), "second": BodyTag}],
        tagId=BodyTag + 1,
    )
