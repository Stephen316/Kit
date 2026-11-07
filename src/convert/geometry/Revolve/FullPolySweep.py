# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.geometry.Revolve.FullFaces import BuildFullFaces
from convert.geometry.Revolve.FullRings import BuildFullRings
from convert.geometry.Revolve.SweepInput import CheckSweepFrame, OrientMeridian
from convert.geometry.Revolve.SweepModel import BuildSweepModel
from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# a closed angular orbit reconstructs only the swept meridian sides
def BuildFullSweep(
    BodyId: str,
    Meridian: tuple[tuple[float, float], ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
) -> BrepModel:
    if not BodyId:
        raise ValueError("Revolve body identity is required")
    CheckSweepFrame(AxisOrigin, AxisDirection, Radial)
    Profile = OrientMeridian(Meridian, AllowAxis=True)
    Frame = Transform(
        AxisOrigin, Radial, CrossVector(AxisDirection, Radial), AxisDirection
    )
    Prefix = f"{BodyId}-sweep"
    Vertices, Curves, Rings = BuildFullRings(Prefix, Profile, Frame)
    Surfaces, Faces, Loops, Coedges = BuildFullFaces(Prefix, Profile, Frame, Rings)
    return BuildSweepModel(
        BodyId,
        Prefix,
        Curves,
        Surfaces,
        Vertices,
        tuple(Rings.values()),
        Faces,
        Loops,
        Coedges,
    )
