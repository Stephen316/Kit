from collections.abc import Mapping
from math import degrees as Degrees, isclose as IsClose

from convert.adapters.freecad.Archive import Quaternion
from convert.adapters.freecad.EditPlaneRev.PlanePoseExpr import PlanePoseExpr
from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import PlaneRevPlan
from convert.adapters.freecad.EditPlaneRev.PlaneSweepExpr import PlaneSweepExpr
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.PlaneRev.PlaneGraph import PlaneGraph
from convert.adapters.freecad.EditRead.PlaneRev.PlaneNativeExpr import CheckPlaneExpr
from convert.adapters.freecad.EditRead.Revolve.RevControls import CheckRevVector
from convert.adapters.freecad.EditRead.Revolve.RevPose import RotateRevAxis
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat, EditScalar
from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import RotatePlane
from convert.formats.Fusion.Revolves.PlaneRevInputs import ProfileLines
from convert.formats.Fusion.Revolves.PlaneSweep import DerivePlaneSpan
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import KTransformIdentity, Transform
from interchange.serialization.EncodeData import ToData


# native datum poses independently corroborate edited literals and immutable source pivots
def ReadTargetPoses(
    Graph: PlaneGraph,
    PlanValue: PlaneRevPlan,
    Aliases: dict[str, str],
    AngleEdits: dict[str, tuple[float, str]],
) -> tuple[Transform, ...]:
    Frames: list[Transform] = []
    for Native, Target in zip(Graph.Targets, PlanValue.Targets, strict=True):
        ZeroFrame = ToData(Target.ZeroFrame)
        if not isinstance(ZeroFrame, Mapping):
            raise ValueError(
                "FreeCAD editable plane Revolve has an invalid source frame"
            )
        PoseText = PlanePoseExpr(
            PlanValue.AxisOrigin,
            Target.RotationAxis,
            Target.ZeroFrame.origin,
            Quaternion(ZeroFrame),
            f"Parameters.{Aliases[Target.AngleParamId]}",
        )
        CheckPlaneExpr(Native, (("Placement", PoseText),))
        Frame = RotatePlane(Target.ZeroFrame, AngleEdits[Target.AngleParamId][0])
        CheckEditFrame(Native, "Placement", Frame)
        Frames.append(Frame)
    return tuple(Frames)


# the evaluated limits must corroborate the solver angle and world placement
def CheckPlaneSweep(
    Graph: PlaneGraph,
    PlanValue: PlaneRevPlan,
    StepValue: FeatureStep,
    Profile: Sketch,
    Frames: tuple[Transform, ...],
) -> None:
    Native = Graph.Feature
    IsCentered = len(Frames) == 2
    CheckRevVector(Native, "Axis", PlanValue.AxisDirection)
    CheckRevVector(Native, "Base", PlanValue.AxisOrigin)
    AxisLink = EditChild(Native, "AxisLink", "App::PropertyLinkSub", "LinkSub")
    if len(AxisLink) or AxisLink.attrib != {"value": "", "count": "0"}:
        raise ValueError("FreeCAD editable plane Revolve axis link changed")
    for Field, TypeName, TagName, Expected in (
        ("Solid", "App::PropertyBool", "Bool", "true"),
        ("Symmetric", "App::PropertyBool", "Bool", "true" if IsCentered else "false"),
        ("FaceMakerClass", "App::PropertyString", "String", "Part::FaceMakerBullseye"),
    ):
        if EditScalar(Native, Field, TypeName, TagName) != Expected:
            raise ValueError(f"FreeCAD editable plane Revolve {Field} changed")
    Expressions = PlaneSweepExpr(
        tuple(Value.name for Value in Graph.Targets),
        PlanValue.AxisOrigin,
        PlanValue.AxisDirection,
        PlanValue.SketchFrame.z_axis,
    )
    CheckPlaneExpr(Native, Expressions)
    Direction, Start, EndValue = DerivePlaneSpan(
        PlanValue.SketchFrame,
        ProfileLines(StepValue, Profile),
        PlanValue.AxisOrigin,
        PlanValue.AxisDirection,
        Frames,
    )
    Angle = EditFloat(
        EditChild(Native, "Angle", "App::PropertyFloatConstraint", "Float"), "value"
    )
    if Direction != PlanValue.AxisDirection or not IsClose(
        Angle,
        Degrees(EndValue - Start),
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError(
            "FreeCAD editable plane Revolve angle disagrees with its targets"
        )
    CheckSweepPose(Graph, PlanValue, (Start + EndValue) / 2.0 if IsCentered else 0.0)


# the initial seed is already in world coordinates while recomputes store the live midpoint
def CheckSweepPose(Graph: PlaneGraph, PlanValue: PlaneRevPlan, Center: float) -> None:
    Identity = KTransformIdentity
    if not Graph.SketchEntry:
        CheckEditFrame(Graph.Feature, "Placement", Identity, Optional=True)
        return
    Direction = PlanValue.AxisDirection
    Frame = Transform(
        PlanValue.AxisOrigin,
        RotateRevAxis(Direction, Identity.x_axis, Center),
        RotateRevAxis(Direction, Identity.y_axis, Center),
        RotateRevAxis(Direction, Identity.z_axis, Center),
    )
    CheckEditFrame(Graph.Feature, "Placement", Frame)
