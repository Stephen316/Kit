# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.brep.surfaces.BrepSurfaces import BrepSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepFace,
    BrepFaceUse,
    BrepRegion,
    BrepShell,
    BrepShellUse,
)


# closed analytic carriers share a single untrimmed face and solid shell structure
def BuildWholeSolid(BodyId: str, Surface: BrepSurface) -> BrepModel:
    Prefix = f"{BodyId}-sweep"
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
        raise ValueError("Invalid reconstructed whole Revolve: " + "; ".join(Errors))
    return Model
