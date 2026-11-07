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
from convert.geometry.Revolve.SweepRims import BuildRim
from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepFaceUse,
    BrepRegion,
    BrepShell,
    BrepShellUse,
)
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
    FaceUses = tuple(
        BrepFaceUse(f"{FaceValue.id}-use", FaceValue.id) for FaceValue in Faces
    )
    Shell = BrepShell(
        f"{Prefix}-shell", tuple(Value.id for Value in FaceUses), closed=True
    )
    ShellUse = BrepShellUse(f"{Shell.id}-use", Shell.id)
    Region = BrepRegion(f"{Prefix}-region", (ShellUse.id,))
    BodyValue = BrepBody(f"{Prefix}-body", (Region.id,), design_body_id=BodyId)
    Model = BrepModel(
        curves=StartCurves + EndCurves + ArcCurves,
        surfaces=Surfaces,
        vertices=StartVertices + EndVertices,
        edges=StartEdges + EndEdges + ArcEdges,
        coedges=Coedges,
        loops=Loops,
        faces=Faces,
        face_uses=FaceUses,
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(BodyValue,),
    )
    Errors = Model.validate(frozenset((BodyId,)))
    if Errors:
        raise ValueError("Invalid reconstructed Revolve solid: " + "; ".join(Errors))
    return Model
