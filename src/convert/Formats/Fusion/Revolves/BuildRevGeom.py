from math import isclose as IsClose, tau as FullTurn

from convert.Formats.Fusion.Revolves.BodyMeridian import ReadMeridian
from convert.Formats.Fusion.Revolves.CircleMeridian import ReadTorusFrame
from convert.Formats.Fusion.Revolves.RevProfile import ReadRevProfile
from convert.Formats.Fusion.Revolves.SphereMeridian import ReadSphereAxis
from convert.Geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.Geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.Geometry.Revolve.SphereSweep import BuildSphere
from convert.Geometry.Revolve.SweepMetrics import MeasureFullTurn, MeasureSweep
from convert.Geometry.Revolve.TorusSweep import BuildTorusSweep
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.Transform import Transform


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
