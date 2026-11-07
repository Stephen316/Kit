# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from math import pi as Pi

from convert.geometry.Revolve.TorusBounds import GetTorusBounds
from interchange.brep.surfaces.BrepSurfaces import TorusSurface
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepFace,
    BrepFaceUse,
    BrepRegion,
    BrepShell,
    BrepShellUse,
)
from interchange.brep.validation.RingTorusValidate import IsRingTorus
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# a full circle sweep closes analytically without invented trims or seam entities
def BuildTorusSweep(
    BodyId: str,
    Center: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    MajorRadius: float,
    MinorRadius: float,
) -> tuple[BrepModel, float, float, BoundingBox]:
    if not isinstance(BodyId, str) or not BodyId.strip():
        raise ValueError("Torus Revolve requires a design body identity")
    Prefix = f"{BodyId}-sweep"
    Surface = TorusSurface(
        f"{Prefix}-surface", Center, AxisDirection, Radial, MajorRadius, MinorRadius
    )
    if not IsRingTorus(Surface):
        raise ValueError("Torus Revolve requires a finite orthonormal ring torus")
    SurfaceArea = 4.0 * Pi * Pi * (MajorRadius * MinorRadius)
    Volume = SurfaceArea * (MinorRadius * 0.5)
    Bounds = GetTorusBounds(Center, AxisDirection, MajorRadius, MinorRadius)
    if not (
        IsFinite(Volume)
        and Volume > 0.0
        and IsFinite(SurfaceArea)
        and SurfaceArea > 0.0
        and IsFiniteSpace(Bounds.minimum)
        and IsFiniteSpace(Bounds.maximum)
    ):
        raise ValueError("Torus Revolve measures exceed finite geometry")
    FaceValue = BrepFace(f"{Prefix}-face", Surface.id, ())
    FaceUse = BrepFaceUse(f"{FaceValue.id}-use", FaceValue.id)
    Shell = BrepShell(f"{Prefix}-shell", (FaceUse.id,), closed=True)
    ShellUse = BrepShellUse(f"{Shell.id}-use", Shell.id)
    Region = BrepRegion(f"{Prefix}-region", (ShellUse.id,))
    BodyValue = BrepBody(f"{Prefix}-body", (Region.id,), design_body_id=BodyId)
    Model = BrepModel(
        surfaces=(Surface,),
        faces=(FaceValue,),
        face_uses=(FaceUse,),
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(BodyValue,),
    )
    Errors = Model.validate(frozenset((BodyId,)))
    if Errors:
        raise ValueError("Invalid reconstructed Torus Revolve: " + "; ".join(Errors))
    return Model, Volume, SurfaceArea, Bounds
