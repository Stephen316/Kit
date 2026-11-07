# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    Profile = OrientMeridian(Meridian)
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
        f"{Prefix}-end", Profile, Frame, EndRadial
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
    return BuildSweepModel(
        BodyId,
        Prefix,
        StartCurves + EndCurves + ArcCurves,
        Surfaces,
        StartVertices + EndVertices,
        StartEdges + EndEdges + ArcEdges,
        Faces,
        Loops,
        Coedges,
    )
