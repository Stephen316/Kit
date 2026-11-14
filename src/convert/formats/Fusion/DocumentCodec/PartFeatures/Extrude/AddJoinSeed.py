from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    BodyTagInfo,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    BodyRecipeOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


def AddJoinSeedMut(
    Author: AuthorState,
    Prefix: str,
    Count: int,
    Operations: tuple[int, ...],
    Label: FaceLabel,
) -> dict[str, object]:
    Author.Allocate(
        Prefix + "join_recipe", "ASMRecipe", Fields={"m_Recipe": BodyRecipeOf(Label)}
    )
    Author.Allocate(Prefix + "join_progenitor", "BodyProgenitor")
    Author.Change(
        Prefix + "join_progenitor",
        bodyUuid=str(MakeUuid()),
        featureTagOccMap=[
            {"key": BodyTagInfo(Author, Count, Operation), "value": 1}
            for Operation in Operations
        ],
        rRefBodyOfTagInherit=Author.Reference(Prefix + "join_recipe"),
    )
    return {"first": Author.Reference(Prefix + "join_progenitor"), "second": Count + 3}
