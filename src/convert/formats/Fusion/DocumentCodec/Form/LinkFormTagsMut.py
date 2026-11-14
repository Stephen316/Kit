from convert.formats.Fusion.DocumentCodec.Form.FormLabels import FormLabel, FormLabels
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def WindowValues(
    Author: AuthorState, LabelValue: FormLabel
) -> list[list[dict[str, object]]]:
    return [
        [
            Author.MakeGroup(
                "TsEntityProgInfoValue",
                dict(
                    faceIndex=Window.Face,
                    uHigh=Window.UHigh,
                    uLow=Window.ULow,
                    vHigh=Window.VHigh,
                    vLow=Window.VLow,
                ),
            )
        ]
        for Window in LabelValue.Windows
    ]


def TagInfo(Author: AuthorState, Labels: tuple[FormLabel, ...]) -> list[object]:
    Encoded = tuple(LabelValue.Label.encode("ascii") for LabelValue in Labels)
    Offsets = [0]
    for LabelText in Encoded:
        Offsets.append(Offsets[-1] + len(LabelText))
    return [
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


def LinkFormTagsMut(Author: AuthorState, SpecValue: FormSpec) -> None:
    Reference = Author.Reference
    Labels = FormLabels(SpecValue.Body)
    for LabelValue in Labels:
        Author.Change(
            "form_label_" + LabelValue.Label,
            entityType=LabelValue.EntityType,
            tsEntityProgenitors=WindowValues(Author, LabelValue),
        )
    Author.Change(
        "form_node_tags",
        ProgenitorTagVec=[
            {
                "first": Reference("form_label_" + LabelValue.Label),
                "second": int(LabelValue.Label),
            }
            for LabelValue in Labels
        ],
        tagId=max((int(LabelValue.Label) for LabelValue in Labels), default=0) + 1,
    )
    Author.Change(
        "body_progenitor",
        bodyUuid=Author.BodyId,
        featureTagOccMap=[
            {"key": TagInfo(Author, Labels), "value": Author.Policy.BodyOccurrenceCount}
        ],
    )
    Author.Change(
        "form_feature_tags",
        ProgenitorTagVec=[{"first": Reference("body_progenitor"), "second": 1}],
        tagId=2,
    )
