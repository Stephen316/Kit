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
