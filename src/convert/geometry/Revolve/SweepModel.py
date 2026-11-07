# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.brep.curves.BrepCurves import BrepCurve
from interchange.brep.surfaces.BrepSurfaces import BrepSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
)


# all solid sweeps need the same closed shell ownership and validation
def BuildSweepModel(
    BodyId: str,
    Prefix: str,
    Curves: tuple[BrepCurve, ...],
    Surfaces: tuple[BrepSurface, ...],
    Vertices: tuple[BrepVertex, ...],
    Edges: tuple[BrepEdge, ...],
    Faces: tuple[BrepFace, ...],
    Loops: tuple[BrepLoop, ...],
    Coedges: tuple[BrepCoedge, ...],
) -> BrepModel:
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
        curves=Curves,
        surfaces=Surfaces,
        vertices=Vertices,
        edges=Edges,
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
