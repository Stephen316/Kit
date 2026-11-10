# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.geometry.Revolve.SweepArcs import BuildArcs
from convert.geometry.Revolve.SweepFaces import BuildFaces
from convert.geometry.Revolve.SweepFrame import RotateRadial
from convert.geometry.Revolve.SweepInput import CheckSweepInput, OrientMeridian
from convert.geometry.Revolve.SweepModel import BuildSweepModel
from convert.geometry.Revolve.SweepRims import BuildRim
from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# bounded polygon sweeps reconstruct a closed analytic body from source geometry
def BuildPolySweep(
    BodyId: str,
    Meridian: tuple[tuple[float, float], ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    StartRadians: float,
    EndRadians: float,
) -> BrepModel:
    CheckSweepInput(BodyId, AxisOrigin, AxisDirection, Radial, StartRadians, EndRadians)
    Profile = OrientMeridian(Meridian, AllowAxis=True)
    Frame = Transform(
        AxisOrigin, Radial, CrossVector(AxisDirection, Radial), AxisDirection
    )
    StartRadial = RotateRadial(Frame, StartRadians)
    EndRadial = RotateRadial(Frame, EndRadians)
    Prefix = f"{BodyId}-sweep"
    StartVertices, StartCurves, StartEdges = BuildRim(
        f"{Prefix}-start", Profile, Frame, StartRadial
    )
    EndVertices, EndCurves, EndEdges = BuildRim(
        f"{Prefix}-end", Profile, Frame, EndRadial, (StartVertices, StartEdges)
    )
    ArcCurves, ArcEdges = BuildArcs(
        f"{Prefix}-orbit",
        Profile,
        Frame,
        StartVertices,
        EndVertices,
        StartRadians,
        EndRadians,
    )
    Surfaces, Faces, Loops, Coedges = BuildFaces(
        Prefix, Profile, Frame, StartRadial, EndRadial, StartEdges, EndEdges, ArcEdges
    )
    RetainedVertices = tuple(
        Value
        for Initial, Value in zip(StartVertices, EndVertices, strict=True)
        if Value is not Initial
    )
    RetainedEdges = tuple(
        Value
        for Initial, Value in zip(StartEdges, EndEdges, strict=True)
        if Value is not Initial
    )
    return BuildSweepModel(
        BodyId,
        Prefix,
        StartCurves + EndCurves + ArcCurves,
        Surfaces,
        StartVertices + RetainedVertices,
        StartEdges
        + RetainedEdges
        + tuple(Value for Value in ArcEdges if Value is not None),
        Faces,
        Loops,
        Coedges,
    )
