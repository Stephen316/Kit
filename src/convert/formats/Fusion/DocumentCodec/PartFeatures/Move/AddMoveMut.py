from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    KBodyOperationType,
    BodyRecipeOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Move.MoveSolid import MoveFrame
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import (
    FocusRole,
)

KMoveModes: dict[str, object] = dict(moveMethodType=5, point2PositionCSType=1)


def MoveEntries(Feature: MoveSpec) -> list[float]:
    CosValue, SinValue, ShiftX, ShiftY, _ = MoveFrame(Feature)
    LiftCm = Feature.OffsetMm[2] / 10.0
    MatrixRows = (
        (CosValue, -SinValue, 0.0, ShiftX),
        (SinValue, CosValue, 0.0, ShiftY),
        (0.0, 0.0, 1.0, LiftCm),
        (0.0, 0.0, 0.0, 1.0),
    )
    return [float(Value) + 0.0 for RowValue in MatrixRows for Value in RowValue]


def AddMoveMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, MoveSpec):
        raise ValueError("Fusion part move authoring requires a move feature")
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcMoveFeature", None)
    AddNodeMut(Author, Prefix + "target", "ModelDataRef", MainRole)
    AddNodeMut(Author, Prefix + "target_body", "DRBody", MainRole)
    AddNodeMut(Author, Prefix + "matrix", "DcMoveMatrix", MainRole)
    Label = Stage.Before.BodyLabel
    Author.Allocate(Prefix + "target_cache", "ETCachedMatrix3d")
    Recipe: dict[str, object] = {"m_Recipe": BodyRecipeOf(Label)}
    Author.Allocate(Prefix + "target_recipe", "ASMRecipe", Fields=Recipe)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(
        Prefix + "target",
        dataRefs=[Reference(Prefix + "target_body")],
        caches=[Reference(Prefix + "target_cache")],
        trackingType=4,
    )
    Author.Change(
        Prefix + "target_body",
        rRecipe=Reference(Prefix + "target_recipe"),
        rScope=PartScope(Author),
        refBodies=[Reference(FocusRole(Author, "dc_body"))],
        trackingType=8,
        operIdTypeMap=[{"key": int(Label.PrimaryId), "value": KBodyOperationType}],
    )
    Author.Change(
        Prefix + "matrix",
        moveTransform={"entries": MoveEntries(Feature)},
        rFeature=Reference(MainRole),
        **KMoveModes,
    )
    Author.Change(MainRole, dcMoveMatrix=Reference(Prefix + "matrix"))
    return [Prefix + "target", Prefix + "target_body", Prefix + "matrix"]
