from dataclasses import replace as Replace
from math import degrees as Degrees, pi as HalfTurn, radians as Radians

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import ReadPlaneRev
from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import RotatePlane
from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from convert.formats.Fusion.Revolves.PlaneRevInputs import ProfileLines
from convert.formats.Fusion.Revolves.PlaneSweep import DerivePlaneSpan
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.records.RecordParameter import Expression
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# original source captures cover signed single limits and unordered paired limits
KPlaneCases = KStudyPath / "revolveto-b1d196f65c46"


# endpoint roots and editable controls must stay tied to the authored plane identities
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "Angles", "Interval"),
    (
        ("positive_plane", (45.0,), (0.0, 135.0)),
        ("negative_plane", (-35.0,), (0.0, 35.0)),
        ("two_planes", (45.0, -35.0), (135.0, 215.0)),
    ),
)
def CheckPlanePlan(
    Capture: str, Angles: tuple[float, ...], Interval: tuple[float, float]
) -> None:
    DocValue = OpenDocument(KPlaneCases / f"{Capture}.f3d", StrictMode=False)
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, PlaneRevolve)
    PlanValue = ReadPlaneRev(DocValue, Feature)
    assert PlanValue is not None
    Picks = {Value.id: Value for Value in DocValue.selections}
    assert PlanValue.TargetPlaneIds == tuple(
        Picks[Identity].path[0].entity_id for Identity in Definition.PlaneSelectionIds
    )
    assert tuple(
        Degrees(Target.AngleRadians) for Target in PlanValue.Targets
    ) == Pytest.approx(Angles)
    assert (
        Degrees(PlanValue.StartRadians),
        Degrees(PlanValue.EndRadians),
    ) == Pytest.approx(Interval)
    EndTarget = PlanValue.Targets[PlanValue.EndPlaneIndex]
    assert (
        EndTarget.SweepSign * EndTarget.AngleRadians + EndTarget.RootTurns * HalfTurn
        == Pytest.approx(PlanValue.EndRadians)
    )
    Restored = CadDocument.FromJson(DocValue.ToJson())
    assert ReadPlaneRev(Restored, Restored.feature_timeline[-1]) == PlanValue


# coincidental frames and stale source references cannot qualify as live datum controls
@KRequiresCodec
def CheckPlanGuard() -> None:
    DocValue = OpenDocument(KPlaneCases / "two_planes.f3d", StrictMode=False)
    Feature = DocValue.feature_timeline[-1]
    PlaneValue, *OtherPlanes = DocValue.support_planes
    Missing = Replace(PlaneValue, attributes={})
    assert (
        ReadPlaneRev(Replace(DocValue, support_planes=(Missing, *OtherPlanes)), Feature)
        is None
    )
    WrongAngle = Replace(
        PlaneValue,
        transform=Replace(PlaneValue.transform, origin=PlaneValue.transform.y_axis),
    )
    assert (
        ReadPlaneRev(
            Replace(DocValue, support_planes=(WrongAngle, *OtherPlanes)), Feature
        )
        is None
    )
    *Targets, AxisPick = DocValue.selections
    WrongAxis = Replace(AxisPick, query={**AxisPick.query, "axis": "X"})
    assert (
        ReadPlaneRev(Replace(DocValue, selections=(*Targets, WrongAxis)), Feature)
        is None
    )
    BodyValue = DocValue.bodies[0]
    assert BodyValue.topology is not None
    WrongBody = Replace(BodyValue, topology=Replace(BodyValue.topology, volume=1.0))
    assert ReadPlaneRev(Replace(DocValue, bodies=(WrongBody,)), Feature) is None


# a verified edited scalar can drive another export using original axis and pivot evidence
@KRequiresCodec
def CheckPlanReedit() -> None:
    DocValue = OpenDocument(KPlaneCases / "positive_plane.f3d", StrictMode=False)
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, PlaneRevolve)
    PlanValue = ReadPlaneRev(DocValue, Feature)
    assert PlanValue is not None
    (Target,) = PlanValue.Targets
    (SketchValue,) = DocValue.sketches
    (BodyValue,) = DocValue.bodies
    assert BodyValue.topology is not None
    PlaneValue, SketchPlane = DocValue.support_planes
    Angle = Radians(-20.0)
    Changed = Replace(PlaneValue, transform=RotatePlane(Target.ZeroFrame, Angle))
    _, Start, EndValue = DerivePlaneSpan(
        PlanValue.SketchFrame,
        ProfileLines(Feature, SketchValue),
        PlanValue.AxisOrigin,
        PlanValue.AxisDirection,
        (Changed.transform,),
    )
    Updated = Replace(Definition, StartRadians=Start, EndRadians=EndValue)
    Final = Replace(Feature, definition=Updated)
    Model, Volume, AreaValue, Bounds = BuildRevGeom(
        BodyValue.id,
        Final,
        Updated,
        (Start, EndValue),
        SketchValue,
        PlanValue.SketchFrame,
    )
    Rebuilt = Replace(
        BodyValue,
        topology=Replace(
            BodyValue.topology,
            volume=Volume,
            surface_area=AreaValue,
            bounding_box=Bounds,
        ),
    )
    Edited = Replace(
        DocValue,
        support_planes=(Changed, SketchPlane),
        bodies=(Rebuilt,),
        brep=Model,
        parameters=tuple(
            (
                Replace(
                    Param,
                    value=Replace(Param.value, value=Angle),
                    expression=Expression("-20 deg", language="freecad"),
                )
                if Param.id == Target.AngleParamId
                else Param
            )
            for Param in DocValue.parameters
        ),
        feature_timeline=DocValue.feature_timeline[:-1] + (Final,),
    )
    Result = ReadPlaneRev(Edited, Final)
    assert Result is not None
    assert Degrees(Result.EndRadians) == Pytest.approx(20.0)
    assert Result.Targets[0].AngleRadians == Angle
