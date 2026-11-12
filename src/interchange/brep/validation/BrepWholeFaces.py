from collections import Counter

from interchange.brep.surfaces.BrepSurfaces import SphereSurface, TorusSurface
from interchange.brep.validation.BrepView import BrepView
from interchange.brep.validation.RingTorusValidate import IsRingTorus
from interchange.brep.validation.SphereValidate import IsFullSphere


# a loopless face is whole only when it uniquely bounds a closed solid shell
def GetWholeFaces(ModelValue: BrepView) -> frozenset[str]:
    Surfaces = {
        Surface.id
        for Surface in ModelValue.surfaces
        if (isinstance(Surface, TorusSurface) and IsRingTorus(Surface))
        or (isinstance(Surface, SphereSurface) and IsFullSphere(Surface))
    }
    if not Surfaces:
        return frozenset()
    RegionOwners = Counter(
        KeyValue for BodyValue in ModelValue.bodies for KeyValue in BodyValue.region_ids
    )
    UseOwners = Counter(
        KeyValue for Region in ModelValue.regions for KeyValue in Region.shell_use_ids
    )
    ShellUses = {Value.id: Value for Value in ModelValue.shell_uses}
    ShellOwners = Counter(Value.shell_id for Value in ModelValue.shell_uses)
    SolidShells = {
        ShellUses[KeyValue].shell_id
        for Region in ModelValue.regions
        if Region.solid and RegionOwners[Region.id] == 1
        for KeyValue in Region.shell_use_ids
        if KeyValue in ShellUses
        and UseOwners[KeyValue] == 1
        and ShellOwners[ShellUses[KeyValue].shell_id] == 1
    }
    FaceUseOwners = Counter(
        KeyValue for Shell in ModelValue.shells for KeyValue in Shell.face_use_ids
    )
    ClosedUses = {
        Shell.face_use_ids[0]
        for Shell in ModelValue.shells
        if Shell.id in SolidShells
        and Shell.closed
        and len(Shell.face_use_ids) == 1
        and FaceUseOwners[Shell.face_use_ids[0]] == 1
    }
    FaceOwners = Counter(Value.face_id for Value in ModelValue.face_uses)
    ClosedFaces = {
        Value.face_id
        for Value in ModelValue.face_uses
        if Value.id in ClosedUses and FaceOwners[Value.face_id] == 1
    }
    return frozenset(
        FaceValue.id
        for FaceValue in ModelValue.faces
        if not FaceValue.loop_ids
        and FaceValue.surface_id in Surfaces
        and FaceValue.id in ClosedFaces
    )
