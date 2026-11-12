from dataclasses import dataclass as MakeDataClass, replace as Replace
from math import isclose as IsClose, pi as HalfTurn

from convert.adapters.freecad.EditPlaneRev.PlaneRevScope import ReadPlaneScope
from convert.adapters.freecad.EditPlaneRev.PlaneTargetPlans import ReadTargetPlans
from convert.adapters.freecad.EditPlaneRev.PlaneTargetData import PlaneRevTarget
from convert.adapters.freecad.EditRev.RevBodyProof import CheckRevBody
from convert.adapters.freecad.EditRev.RevProfileProof import CheckRevProfile
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# native editable plan preserves source role order and geometric endpoint assignment
@MakeDataClass(frozen=True, slots=True)
class PlaneRevPlan:
    SketchId: str
    AxisOrigin: SpaceVector
    AxisDirection: SpaceVector
    SketchFrame: Transform
    Targets: tuple[PlaneRevTarget, ...]
    InactiveParamId: str
    StartRadians: float
    EndRadians: float
    StartPlaneIndex: int | None
    EndPlaneIndex: int

    # the consumer can bind targets to original native datum names
    @property
    def TargetPlaneIds(self) -> tuple[str, ...]:
        return tuple(Target.PlaneId for Target in self.Targets)


# source role order is preserved even when it differs from endpoint order
def BuildPlanePlan(
    DocValue: CadDocument,
    FeatureValue: FeatureStep,
    Definition: PlaneRevolve,
    SketchValue: Sketch,
    SketchPlane: SupportPlane,
) -> PlaneRevPlan:
    Targets, Roots, Inactive = ReadTargetPlans(
        DocValue, FeatureValue, Definition, SketchValue, SketchPlane
    )
    if len(Roots) == 1:
        StartIndex, EndIndex = None, 0
        Start, EndValue = 0.0, Roots[0]
    else:
        EndIndex = 0 if Roots[0] < Roots[1] else 1
        StartIndex = 1 - EndIndex
        Start, EndValue = Roots[StartIndex], Roots[EndIndex] + HalfTurn
        Targets[EndIndex] = Replace(
            Targets[EndIndex], RootTurns=Targets[EndIndex].RootTurns + 1
        )
        if Roots[StartIndex] - Roots[EndIndex] <= 1e-9:
            raise ValueError("FreeCAD editable plane Revolve target planes coincide")
    if not all(
        IsClose(Cached, Expected, rel_tol=0.0, abs_tol=1e-9)
        for Cached, Expected in (
            (Definition.StartRadians, Start),
            (Definition.EndRadians, EndValue),
        )
    ):
        raise ValueError("FreeCAD editable plane Revolve span disagrees with targets")
    return PlaneRevPlan(
        SketchValue.id,
        Definition.AxisOrigin,
        Definition.AxisDirection,
        SketchPlane.transform,
        tuple(Targets),
        Inactive,
        Definition.StartRadians,
        Definition.EndRadians,
        StartIndex,
        EndIndex,
    )


# live qualification requires exact native history and complete rebuilt body corroboration
def ReadPlaneRev(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> PlaneRevPlan | None:
    Definition = FeatureValue.definition
    if not isinstance(Definition, PlaneRevolve):
        return None
    try:
        SketchValue, SketchPlane, BodyValue = ReadPlaneScope(
            DocValue, FeatureValue, len(Definition.PlaneSelectionIds)
        )
        CheckRevProfile(FeatureValue, SketchValue)
        PlanValue = BuildPlanePlan(
            DocValue, FeatureValue, Definition, SketchValue, SketchPlane
        )
        CheckRevBody(
            BodyValue,
            DocValue,
            FeatureValue,
            Definition,
            (PlanValue.StartRadians, PlanValue.EndRadians),
            SketchValue,
            SketchPlane,
        )
    except (AttributeError, IndexError, KeyError, OverflowError, TypeError, ValueError):
        return None
    return PlanValue
