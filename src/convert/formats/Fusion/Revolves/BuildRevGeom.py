from math import isclose as IsClose, tau as FullTurn

from convert.formats.Fusion.Revolves.BodyMeridian import ReadMeridian
from convert.formats.Fusion.Revolves.CircleMeridian import ReadTorusFrame
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from convert.formats.Fusion.Revolves.SphereMeridian import ReadSphereAxis
from convert.geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.geometry.Revolve.SphereSweep import BuildSphere
from convert.geometry.Revolve.SweepMetrics import MeasureFullTurn, MeasureSweep
from convert.geometry.Revolve.TorusSweep import BuildTorusSweep
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# the profile family and interval determine the appropriate closed analytic topology
def BuildRevGeom(
    BodyId: str,
    StepValue: FeatureStep,
    Definition: PlaneRevolve | AngularRevolve,
    Interval: tuple[float, float],
    SketchValue: Sketch,
    FrameValue: Transform,
) -> tuple[BrepModel, float, float, BoundingBox]:
    IsFull = IsClose(Interval[1] - Interval[0], FullTurn, rel_tol=0.0, abs_tol=1e-10)
    Profile = ReadRevProfile(StepValue, SketchValue)
    AxisOrigin, AxisDirection = Definition.AxisOrigin, Definition.AxisDirection
    if isinstance(Profile, CircleGeometry):
        if not IsFull:
            raise ValueError("Fusion circular Revolve solid requires one full turn")
        Center, Radial, MajorRadius = ReadTorusFrame(
            FrameValue, Profile, AxisOrigin, AxisDirection
        )
        return BuildTorusSweep(
            BodyId, Center, AxisDirection, Radial, MajorRadius, Profile.radius
        )
    if isinstance(Profile, ArcGeometry):
        if not IsFull:
            raise ValueError("Fusion semicircle Revolve solid requires one full turn")
        Center, Direction, Radial = ReadSphereAxis(
            FrameValue, Profile, AxisOrigin, AxisDirection
        )
        return BuildSphere(BodyId, Center, Direction, Radial, Profile.radius)
    Meridian, Radial = ReadMeridian(FrameValue, Profile, AxisOrigin, AxisDirection)
    SweepArgs = (Meridian, AxisOrigin, AxisDirection, Radial)
    if IsFull:
        Model = BuildFullSweep(BodyId, *SweepArgs)
        Volume, AreaValue, Bounds = MeasureFullTurn(*SweepArgs)
    else:
        Model = BuildPolySweep(BodyId, *SweepArgs, *Interval)
        Volume, AreaValue, Bounds = MeasureSweep(*SweepArgs, *Interval)
    return Model, Volume, AreaValue, Bounds
