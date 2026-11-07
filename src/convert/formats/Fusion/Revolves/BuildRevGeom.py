# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import isclose as IsClose, tau as FullTurn

from convert.formats.Fusion.Revolves.BodyMeridian import ReadMeridian
from convert.formats.Fusion.Revolves.CircleMeridian import ReadTorusFrame
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from convert.geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.geometry.Revolve.SweepMetrics import MeasureFullTurn, MeasureSweep
from convert.geometry.Revolve.TorusSweep import BuildTorusSweep
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import CircleGeometry
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
    Meridian, Radial = ReadMeridian(FrameValue, Profile, AxisOrigin, AxisDirection)
    SweepArgs = (Meridian, AxisOrigin, AxisDirection, Radial)
    if IsFull:
        Model = BuildFullSweep(BodyId, *SweepArgs)
        Volume, Area, Bounds = MeasureFullTurn(*SweepArgs)
    else:
        Model = BuildPolySweep(BodyId, *SweepArgs, *Interval)
        Volume, Area, Bounds = MeasureSweep(*SweepArgs, *Interval)
    return Model, Volume, Area, Bounds
