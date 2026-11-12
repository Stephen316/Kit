from math import dist as Distance

from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import (
    IsSameAngPlane,
    VectorCoords,
)
from convert.formats.Fusion.Extrudes.ExtrudeBinding import (
    CheckExtBinding,
    KExtrudeBinding,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.NativePlane import KPlaneFeature, ReadNativePlane
from convert.formats.Fusion.ParamProjection import ParamOrigin, ParamQuantity
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SourceProof.Bindings.BindingRoles import KBindingRoles
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordParameter import Parameter


# a projected datum must identify the same frame and feature independently of its definition
def CheckBindDatum(
    Document: CadDocument, Cached: SupportPlane, OwnerValue: RecordSpan, PlaneId: str
) -> None:
    Candidates = tuple(
        Plane
        for Plane in Document.support_planes
        if Plane.id == PlaneId
        or Plane.attributes.get("fusion.feature_object_id") == OwnerValue.ObjectId
    )
    Origin = Cached.provenance
    if len(Candidates) != 1 or Origin is None:
        raise ValueError("Missing or ambiguous Fusion binding construction datum")
    (Projected,) = Candidates
    Evidence = Projected.provenance
    if (
        Projected.id != PlaneId
        or Projected.id != Cached.id
        or Projected.name != Cached.name
        or Projected.transform != Cached.transform
        or Evidence is None
        or Evidence.native_id != Origin.native_id
        or Evidence.adapter != Origin.adapter
        or Evidence.spans[: len(Origin.spans)] != Origin.spans
        or any(
            Projected.attributes.get(NameValue) != Value
            for NameValue, Value in Cached.attributes.items()
        )
    ):
        raise ValueError("Projected Fusion binding construction datum disagrees")


# checking both controls prevents a valid binding from masking a stale companion parameter
def CheckPlaneParam(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    StepValue: FeatureStep,
    ParamValue: Parameter,
    BindingId: int,
    RoleName: str,
    UnitName: str,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, BindingId, KExtrudeBinding)
    Cursor.Offset = 29
    NativeId = ReadNativeRef(Cursor)
    Native = CheckExtBinding(BulkData, Owners, OwnerId, BindingId, RoleName)
    Origin = ParamValue.provenance
    Attrs = ParamValue.attributes
    if (
        ParamValue.id != f"fusion-parameter-{NativeId}"
        or ParamValue.owner_id != StepValue.id
        or ParamValue.name != Native.ParamName
        or ParamValue.value != ParamQuantity(Native)
        or ParamValue.value.unit != UnitName
        or Attrs.get("fusion.binding_id") != BindingId
        or Attrs.get("fusion.native_role") != RoleName
        or Attrs.get("fusion.owner_object_id") != OwnerId
        or Attrs.get("fusion.owner_class_guid") != KPlaneFeature
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != str(NativeId)
        or Origin.spans
        != ParamOrigin(Owners[NativeId]).spans + ParamOrigin(Owners[BindingId]).spans
    ):
        raise ValueError("Projected Fusion binding construction parameter disagrees")


# matching tolerance follows the independently observed angular and offset caches
def IsSameBindDatum(Method: str, Expected: Transform, Actual: Transform) -> bool:
    if Method == "angle":
        return IsSameAngPlane(Expected, Actual)
    return Distance(
        VectorCoords(Expected.origin), VectorCoords(Actual.origin)
    ) <= 1e-9 and all(
        Distance(VectorCoords(First), VectorCoords(Second)) <= 1e-10
        for First, Second in (
            (Expected.x_axis, Actual.x_axis),
            (Expected.y_axis, Actual.y_axis),
            (Expected.z_axis, Actual.z_axis),
        )
    )


# offset and angle roles are fixed by native authoring controls rather than cached frame type
def DatumBindRoles(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    OwnerValue: RecordSpan,
    StepValue: FeatureStep,
) -> KBindingRoles:
    from convert.formats.Fusion.ConstructionPlane.PlaneControls import ReadPlaneParams
    from interchange.features.BoundPlaneValues import GetDatumFrame
    from interchange.features.FeatureBoundPlane import BoundDatum

    Definition = StepValue.definition
    if StepValue.kind != FeatureKind.KReference or not isinstance(
        Definition, BoundDatum
    ):
        raise ValueError("Unsupported Fusion binding construction plane definition")
    Cached = ReadNativePlane(BulkData, OwnerValue, Owners)
    CheckBindDatum(Document, Cached, OwnerValue, Definition.SupportPlaneId)
    Controls = ReadPlaneParams(BulkData, Owners, Cached)
    if (
        Controls.Method != Definition.Method
        or Controls.ReferenceFrame != Definition.ReferenceFrame
    ):
        raise ValueError("Fusion binding construction plane authoring frame disagrees")
    ScalarRole, ScalarUnit = (
        ("RotateAngle", "rad")
        if Controls.Method == "angle"
        else ("AlongDistance", "cm")
    )
    ParamIds = {Definition.ScalarParameterId, Definition.OffsetParameterId}
    Candidates = tuple(Value for Value in Document.parameters if Value.id in ParamIds)
    if (
        len(Candidates) != 2
        or len(StepValue.parameter_ids) != 2
        or set(StepValue.parameter_ids) != ParamIds
    ):
        raise ValueError("Fusion binding construction plane control set disagrees")
    Params = {Value.id: Value for Value in Candidates}
    Roles = (
        (
            Controls.ScalarBindingId,
            Definition.ScalarParameterId,
            ScalarRole,
            ScalarUnit,
        ),
        (Controls.OffsetBindingId, Definition.OffsetParameterId, "ExtraOffset", "cm"),
    )
    for BindingId, ParamId, RoleName, UnitName in Roles:
        ParamValue = Params.get(ParamId)
        if ParamValue is None:
            raise ValueError("Missing projected Fusion binding construction parameter")
        CheckPlaneParam(
            BulkData,
            Owners,
            OwnerValue.ObjectId,
            StepValue,
            ParamValue,
            BindingId,
            RoleName,
            UnitName,
        )
    Expected = GetDatumFrame(StepValue, Definition, Params)
    if not IsSameBindDatum(Controls.Method, Expected, Cached.transform):
        raise ValueError(
            "Fusion binding construction plane controls miss the cached frame"
        )
    return Roles
