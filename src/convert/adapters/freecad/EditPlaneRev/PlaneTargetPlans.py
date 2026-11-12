from interchange.records.RecordParameter import Parameter
from collections.abc import Mapping
from math import isclose as IsClose, pi as HalfTurn
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectMap
from convert.adapters.freecad.EditPlaneRev.PlaneRevParams import (
    ReadInactive,
    ReadTargetPars,
)
from convert.adapters.freecad.EditPlaneRev.PlaneRevTargets import (
    ReadPlanePicks,
    ReadTargetBase,
    ReadTargetStep,
)
from convert.adapters.freecad.EditPlaneRev.PlaneTargetData import PlaneRevTarget
from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import IsSameAngPlane
from convert.formats.Fusion.Revolves.PlaneRevInputs import ProfileLines
from convert.formats.Fusion.Revolves.PlaneSweep import DerivePlaneSpan
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# each source target retains a live scalar and a corroborating geometric root
def ReadTargetPlans(
    DocValue: CadDocument,
    FeatureValue: FeatureStep,
    Definition: PlaneRevolve,
    SketchValue: Sketch,
    SketchPlane: SupportPlane,
) -> tuple[list[PlaneRevTarget], list[float], str]:
    Frame = SketchPlane.transform
    Profile = ProfileLines(FeatureValue, SketchValue)
    AxisPick, Inputs = ReadPlanePicks(DocValue, FeatureValue, Definition)
    Params = {Value.id: Value for Value in DocValue.parameters}
    Steps = {
        int(Value.provenance.native_id): Value
        for Value in DocValue.feature_timeline[1:-1]
        if Value.provenance is not None and Value.provenance.adapter == "fusion.f3d"
    }
    Inactive = ReadInactive(FeatureValue, Params)
    Targets: list[PlaneRevTarget] = []
    Roots: list[float] = []
    for Index, (PickValue, PlaneValue) in enumerate(Inputs):
        StepValue = ReadTargetStep(FeatureValue, Steps, PickValue, PlaneValue, Index)
        Proof = PlaneValue.attributes.get("fusion.angle_plane")
        if not IsObjectMap(Proof):
            raise ValueError("FreeCAD editable plane has no authored angle evidence")
        AngleId, Radians, ExtraId = ReadTargetPars(
            StepValue, Params, CastValue(Mapping[str, object], Proof)
        )
        ZeroFrame = ReadTargetBase(
            CastValue(Mapping[str, object], Proof),
            AxisPick,
            PlaneValue,
            SketchPlane,
            FeatureValue,
            Radians,
        )
        Construction = StepValue.definition
        if isinstance(Construction, BoundDatum) and (
            Construction.ScalarParameterId != AngleId
            or Construction.OffsetParameterId != ExtraId
            or not IsSameAngPlane(Construction.ReferenceFrame, ZeroFrame)
        ):
            raise ValueError(
                "FreeCAD editable plane typed controls disagree with source"
            )
        Direction, _, RootValue = DerivePlaneSpan(
            Frame,
            Profile,
            Definition.AxisOrigin,
            Definition.AxisDirection,
            (PlaneValue.transform,),
        )
        if Direction != Definition.AxisDirection:
            raise ValueError("FreeCAD editable plane Revolve axis direction disagrees")
        SweepSign = round(DotVector(ZeroFrame.x_axis, Direction))
        Turns = round((RootValue - SweepSign * Radians) / HalfTurn)
        if SweepSign not in (-1, 1) or not IsClose(
            SweepSign * Radians + Turns * HalfTurn, RootValue, rel_tol=0.0, abs_tol=1e-9
        ):
            raise ValueError("FreeCAD editable plane sweep branch is unresolved")
        Targets.append(
            PlaneRevTarget(
                PlaneValue.id,
                StepValue.id,
                AngleId,
                Radians,
                ExtraId,
                ZeroFrame.x_axis,
                ZeroFrame,
                Turns,
                SweepSign,
            )
        )
        Roots.append(RootValue)
    CheckTargetSet(Params, DocValue, Targets, Inactive, SketchPlane)
    return Targets, Roots, Inactive


# exact parameter and plane coverage keeps unrelated controls outside editable revolve
def CheckTargetSet(
    Params: dict[str, Parameter],
    DocValue: CadDocument,
    Targets: list[PlaneRevTarget],
    Inactive: str,
    SketchPlane: SupportPlane,
) -> None:
    if (
        len(Params) != len(DocValue.parameters)
        or Params.keys()
        != {
            Inactive,
            *(
                Identity
                for Target in Targets
                for Identity in (Target.AngleParamId, Target.OffsetParamId)
            ),
        }
        or len({Target.StepId for Target in Targets}) != len(Targets)
        or len({Target.PlaneId for Target in Targets}) != len(Targets)
        or {SketchPlane.id, *(Target.PlaneId for Target in Targets)}
        != {Value.id for Value in DocValue.support_planes}
    ):
        raise ValueError("FreeCAD editable plane Revolve has unrelated controls")
