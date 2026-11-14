from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import (
    FamilyOf,
    IsStateless,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec


def LinkFeatureMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, Children: list[str]
) -> None:
    Reference = Author.Reference
    Stateless = IsStateless(Stage.Feature)
    Unmodeled = Stateless or isinstance(Stage.Feature, PasteSpec)
    Fields: dict[str, object] = dict(
        childNodes=[Reference(RoleName) for RoleName in Children],
        featureBaseName=FamilyOf(Stage.Feature).BaseName,
        featureUserName="" if Stateless else Stage.Feature.FeatureName,
        featureIndex=Stage.FamilyIndex,
        rProgenitorTable=Reference(Prefix + "progenitors"),
        startModelHS=-1 if Unmodeled else Stage.StateId - 1,
        endModelHS=-1 if Unmodeled else Stage.StateId,
    )
    if not Unmodeled:
        Targets = [Prefix + "target"] if Prefix + "target" in Author.Roles else []
        Fields["targetDataRefs"] = [Reference(RoleName) for RoleName in Targets]
    Author.Change(Prefix + "feature", **Fields)
