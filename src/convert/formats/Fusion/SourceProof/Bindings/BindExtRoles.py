from convert.formats.Fusion.Extrudes.ExtrudeControl import ReadExtControls
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.Extrudes.Plane.PlaneExtControl import ReadPlaneCtrl
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SourceProof.Bindings.BindingRoles import KBindingRoles
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude


# native distance slot order differs from the physical order of optional control references
def DistBindRoles(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    Definition: DistanceExtrude,
) -> KBindingRoles:
    Native = ReadExtControls(SelectCursor(BulkData, Owners, OwnerId, KExtrudeGuid))
    if Native.SideMode != Definition.SideMode:
        raise ValueError("Fusion distance binding owner side mode disagrees")
    if Native.SideMode.startswith("symmetric_") and (
        (Native.SecondTaperId is None) != (Definition.SecondTaperId is None)
    ):
        raise ValueError("Fusion distance binding mirrored taper disagrees")
    Roles: tuple[tuple[int | None, str | None, str, str], ...] = (
        (Native.StartId, Definition.StartOffsetId, "ProfileOffset", "cm"),
        (Native.AlongId, Definition.AlongParameterId, "AlongDistance", "cm"),
        (Native.TaperId, Definition.TaperParameterId, "TaperAngle", "rad"),
        (Native.AgainstId, Definition.AgainstParameterId, "AgainstDistance", "cm"),
    )
    if Native.SideMode == "two_sided":
        Roles += (
            (Native.SecondTaperId, Definition.SecondTaperId, "Side2TaperAngle", "rad"),
        )
    return Roles


# selected end offset and selected start offset are distinct authored control roles
def PlaneBindRoles(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    Definition: PlaneExtrude,
) -> KBindingRoles:
    Native = ReadPlaneCtrl(SelectCursor(BulkData, Owners, OwnerId, KExtrudeGuid))
    if Native.Role != Definition.LimitRole:
        raise ValueError("Fusion plane binding owner limit role disagrees")
    OffsetRole = "ProfileOffset" if Native.Role == "start" else "Side1Offset"
    return (
        (Native.OffsetId, Definition.OffsetParameterId, OffsetRole, "cm"),
        (Native.AlongId, Definition.LengthParameterId, "AlongDistance", "cm"),
        (Native.TaperId, Definition.TaperParameterId, "TaperAngle", "rad"),
    )
