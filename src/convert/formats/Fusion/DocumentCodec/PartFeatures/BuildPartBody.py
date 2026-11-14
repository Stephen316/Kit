from dataclasses import replace as ReplaceValue
from time import time_ns as ReadTimeNano

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EmitPartHist import (
    EmitPartHist,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import (
    IsStateless,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart


def TrackedShape(Solid: PrismSolid, Roles: dict[str, int]) -> ShapeBody:
    Tracks = tuple(
        (Label, Roles["f" + str(Index + 1) + "_source_ref"])
        for Label, Index in Solid.Tracks
    )
    return ReplaceValue(BuildShape(Solid), Tracks=Tracks)


def BuildPartBody(
    SpecValue: DocumentSpec, Design: DesignResult
) -> tuple[ContainerPart, ...]:
    if Design.BrepPart is None:
        raise ValueError("Fusion part authoring requires a BRep part identity")
    Policy = AuthorPolicy()
    if Policy.BodyKey != 0:
        raise ValueError("Fusion part journals claim body tag zero first")
    BaseValue, Stages = SolvePart(SpecValue)
    KeptStages = tuple(Stage for Stage in Stages if not IsStateless(Stage.Feature))
    Solids = (() if BaseValue is None else ((BaseValue,),)) + tuple(
        Stage.Bodies for Stage in KeptStages
    )
    StateIds = (() if BaseValue is None else (Policy.HistoryCurrentId,)) + tuple(
        Stage.StateId for Stage in KeptStages
    )
    Payload = EmitPartHist(
        tuple(
            tuple(TrackedShape(Solid, Design.Roles) for Solid in Bodies)
            for Bodies in Solids
        ),
        StateIds,
        Policy.HistoryInitialId,
        float(ReadTimeNano() // 1000),
    )
    return (ContainerPart("Breps.BlobParts/" + Design.BrepPart, Payload),)
