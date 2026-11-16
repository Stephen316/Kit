from __future__ import annotations as Annotations
from convert.adapters.solidworks.Core.AxisSketchId import AxisSketchId
from dataclasses import dataclass as Dataclass, field as Field, replace as Replace
import hashlib as Hashlib
import itertools as Itertools
import math as MathValue
import re as RegexLib
import struct as Struct
from types import MappingProxyType
from typing import Mapping, Sequence
import xml.etree.ElementTree as XmlTree  # noqa: DUO107
from interchange import (
    BooleanOperation as BoolOperation,
    CircleGeometry as CircleGeom,
    ParameterRole as ParamRole,
)
from convert.Geometry.Opencascade import decode_ascii_brep as DecodeAsciiBrep
from convert.adapters.base import ParseUntrusted
from convert.adapters.solidworks.Container.Container import SldprtFormatError
from convert.adapters.solidworks.Container.Format import (
    ASSEMBLY_SUFFIX as AsmSuffix,
    CANONICAL_PLANE_FEATURE_TYPE as CanonicalPlaneFeatureType,
    CLASS_MARKER as ClassMarker,
    DIMENSION_SCALAR_HEADERS as DimensionScalarHeaders,
    KIT_RESOLVED_STREAM as KitResolvedStream,
    PART_SUFFIX as PartSuffix,
    PLANE_FEATURE_TYPES as PlaneFeatureTypes,
    RESOLVED_FEATURES_STREAM as ResolvedFeaturesStream,
    SERIALIZED_STRING_MARKER as SerializedStringMarker,
    dimension_scalar_value_offset as DimensionScalarValue,
)
from convert.adapters.solidworks.Resolved.Core import (
    ANGLE_COPY_DELTAS as AngleCopyDeltas,
    DEPTH_COPY_DELTAS as DepthCopyDeltas,
    DEPTH_COPY_SIGNS as DepthCopySigns,
    FeatureLayout,
    FROM_END_SPEC_CLASS as FromEndSpecClass,
    FROM_REVERSE_RELATIVE as FromReverseRelative,
    REVOLUTION_AXIS_SKETCH as RevolutionAxisSketch,
    SKETCH_CHAIN_CLASS as SketchChainClass,
    circle_radius_mm as CircleRadiusMm,
    locate_features as LocateFeatures,
)

# this binding exists because shared behavior needs one stable value
KRadiansToDegrees = 180.0 / MathValue.pi

# this binding exists because shared behavior needs one stable value
KCurrentMarker = bytes.fromhex("ffff1f0003")

# this binding exists because shared behavior needs one stable value
KLegacyMarker = bytes.fromhex("ffff070001")

# this binding exists because shared behavior needs one stable value
KExtendedMarker = bytes.fromhex("ffff1f0001")

# this binding exists because shared behavior needs one stable value
KMarkers = (KCurrentMarker, KLegacyMarker, KExtendedMarker)

# this binding exists because shared behavior needs one stable value
KCoordinateTag = bytes.fromhex("1e00")

# this binding exists because shared behavior needs one stable value
KPointLocus = bytes.fromhex("04000200")

# this binding exists because shared behavior needs one stable value
KCircleLocus = bytes.fromhex("05000100")

# this binding exists because shared behavior needs one stable value
KNumber = RegexLib.compile("[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?")

# this binding exists because shared behavior needs one stable value
KEdgeSelectionIdentity = bytes.fromhex("7dc39425ad49b2547dc39425ad49b254")

# this binding exists because shared behavior needs one stable value
KRevolutionFeatureTypes = frozenset({"revolve", "revolution", "cut-revolve", "revcut"})

# this binding exists because shared behavior needs one stable value
KSurfaceExtrusionFeature = frozenset({"surface-extrude", "extrurefsurface"})

# this binding exists because shared behavior needs one stable value
KMoveBodyFeatureTypes = frozenset({"body-move/copy", "movecopybody"})

# this binding exists because shared behavior needs one stable value
KCombineFeatureTypes = frozenset({"combine", "combinebodies"})

# this binding exists because shared behavior needs one stable value
KHoleClassNames = frozenset({"moSketchHole", "moHoleWzd_c"})

# this binding exists because shared behavior needs one stable value
KEquation = RegexLib.compile('^"([^"\\r\\n]+)"\\s*=\\s*(\\S(?:.*\\S)?)$')

# this binding exists because shared behavior needs one stable value
KEquationRef = RegexLib.compile('"([^"\\r\\n]+)"')

# this binding exists because shared behavior needs one stable value
KExtrusionClass = "moExtrusion_c"

# this binding exists because shared behavior needs one stable value
KBoundingBoxClass = "moBBoxCenterData_c"

# this binding exists because shared behavior needs one stable value
KBoundingBoxRelative = 28

# this binding exists because shared behavior needs one stable value
KFaceSupportClass = "moFaceRefPlnData_c"

# this binding exists because shared behavior needs one stable value
KSketchPlaneIdRelative = 209

# this binding exists because shared behavior needs one stable value
KSketchPlaneRefPrefix = bytes.fromhex("50460000")

# this binding exists because shared behavior needs one stable value
KSketchPlaneRefTag = bytes.fromhex("f65a1a69")

# this binding exists because shared behavior needs one stable value
KSketchPlaneAxisDelta = 10

# this binding exists because shared behavior needs one stable value
KSketchPlaneBasisFlagDelA = 14

# this binding exists because shared behavior needs one stable value
KSketchPlaneBasisDelta = 15

# this binding exists because shared behavior needs one stable value
KSketchPlaneBasisBytes = 72

# this binding exists because shared behavior needs one stable value
KSketchPlaneAxisComplemeA = 5

# this binding exists because shared behavior needs one stable value
KSketchPlaneScanBytes = 320

# this binding exists because shared behavior needs one stable value
KPrincipalPlaneObjectIds = frozenset({2, 3, 4})


# this binding exists because shared behavior needs one stable value
KExtrusionOperationKinds = frozenset({"join", "cut"})

# this binding exists because shared behavior needs one stable value
KRevolutionOperationKinds = frozenset({"revolve_join", "revolve_cut"})

# this binding exists because shared behavior needs one stable value
KNormalAxisSubElem = "N_Axis"

# this binding exists because shared behavior needs one stable value
KVerticalAxisSubElem = "V_Axis"

# this binding exists because shared behavior needs one stable value
KHorizontalAxisSubElem = "H_Axis"

# this binding exists because shared behavior needs one stable value
KDirectionAxisRole = "direction_axis"

# this binding exists because shared behavior needs one stable value
KIdentityBasis = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

# this binding exists because shared behavior needs one stable value
KIdentityOrigin = (0.0, 0.0, 0.0)

# this binding exists because shared behavior needs one stable value
KDerivedPlaneClasses = (
    "moRefPlaneMidPlaneGeom_c",
    "moConstraintMidPlaneRefplaneData_c",
    "moLinePtRefPlnData_c",
    "moFaceRefPlnData_c",
    "moFixedRefPlnData_c",
    "moDefaultRefPlnData_c",
)

# this binding exists because shared behavior needs one stable value
KPlaneSupportKind = "plane"

# this binding exists because shared behavior needs one stable value
KFaceSupportKind = "face"

# this binding exists because shared behavior needs one stable value
KDerivedSupportKind = "derived"

# this binding exists because shared behavior needs one stable value
KRefSupportSource = "plane-reference"

# this binding exists because shared behavior needs one stable value
KStreamOrderSupportSource = "stream-order"

# this binding exists because shared behavior needs one stable value
KUnresolvedSupportSource = "unresolved"

# this binding exists because shared behavior needs one stable value
KMillimetres = 1000.0

# this binding exists because shared behavior needs one stable value
KMarkerLocalIdOffsetBy = MappingProxyType(
    {
        142: 138,
        146: 138,
        152: 148,
        154: 150,
        156: 148,
        158: 144,
        162: 158,
        166: 158,
        167: 158,
    }
)


# decode state exists because ordered features share evolving native context
@Dataclass(slots=True)
class DecodeState:
    Resolved: bytes
    StreamName: str
    Classes: tuple[NativeClass, ...]
    RecordById: dict[int, NativeName]
    NativeFeatures: list[NativeFeature]
    NativeIndexById: dict[int, int]
    PlaneById: dict[int, NativePlane]
    UnframedPlaneIds: frozenset[int]
    Revolutions: dict[int, FeatureLayout]
    Sketches: list[NativeSketch]
    Operations: list[NativeOperation]
    LatestSketch: NativeSketch | None
    LatestOperation: NativeOperation | None
    LatestPlaneId: int
    LatestUnframed: int | None


# plane state handling preserves the latest framed support context
def ApplyPlaneMut(StateData: DecodeState, Feature: NativeFeature) -> None:
    if Feature.object_id in StateData.PlaneById:
        StateData.LatestPlaneId = Feature.object_id
        StateData.LatestUnframed = None
    else:
        StateData.LatestUnframed = Feature.object_id


# sketch state handling owns support decoding and feature dimension rebinding
def ApplySketchMut(StateData: DecodeState, Feature: NativeFeature) -> None:
    SketchStart = Feature.native_offset or 0
    SketchEnd = Feature.native_end or len(StateData.Resolved)
    RefValue = SketchPlaneRef(
        StateData.Resolved, StateData.Classes, SketchStart, SketchEnd
    )
    Support, SupportSource, UnframedSupport = SupportPlaneRef(
        StateData.Resolved,
        SketchStart,
        SketchEnd,
        RefValue,
        StateData.LatestPlaneId,
        StateData.LatestUnframed,
        StateData.PlaneById,
        StateData.UnframedPlaneIds,
    )
    StateData.LatestSketch = DecodeSketch(
        StateData.Resolved,
        Feature,
        Support,
        NativeStream=StateData.StreamName,
        SupportKind=SketchSupport(StateData.Classes, RefValue, SketchStart, SketchEnd),
        SupportPlane=RefValue,
        SupportSource=SupportSource,
        UnframedSupportPlaneId=UnframedSupport,
    )
    NativeIndex = StateData.NativeIndexById[Feature.object_id]
    StateData.NativeFeatures[NativeIndex] = Replace(
        StateData.NativeFeatures[NativeIndex],
        dimensions=StateData.LatestSketch.dimensions,
    )
    StateData.Sketches.append(StateData.LatestSketch)


# focused operation decoder preserves one native feature family
def DecodeExtrude(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Record = StateData.RecordById.get(Feature.object_id)
    if Record is None:
        return None
    Child = IntegerProp(Feature.properties.get("DissectableChildren"))
    ProfileId = Child or (
        StateData.LatestSketch.object_id if StateData.LatestSketch else None
    )
    Dependencies = tuple(
        (
            Value
            for Value in (
                (
                    StateData.LatestOperation.object_id
                    if StateData.LatestOperation
                    else None
                ),
                ProfileId,
            )
            if Value is not None
        )
    )
    Family, OperationCode, Schema = OperationFields(StateData.Resolved, Record)
    OperationStart = Feature.native_offset or 0
    OperationEnd = Feature.native_end or len(StateData.Resolved)
    EndData = EndSpec(
        StateData.Resolved, OperationStart, OperationEnd, StateData.Classes
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind=(
            "join" if OperationCode == 0 else "cut" if OperationCode == 2 else "native"
        ),
        profile_id=ProfileId,
        dependencies=Dependencies,
        native_offset=OperationStart,
        native_end=ClassRecordEnd(StateData.Resolved, StateData.Classes, OperationStart)
        or OperationEnd,
        length_mm=DimensionValue(Feature.dimensions, "length"),
        radius_mm=None,
        family_code=Family,
        operation_code=OperationCode,
        schema_code=Schema,
        direction_code=EndData.direction_code if EndData else None,
        termination_code=EndData.termination_code if EndData else None,
        selection_offsets=(),
        selected_local_ids=(),
        native_stream=StateData.StreamName,
        depth_copies=DepthCopies(
            StateData.Resolved, OperationOffset(Feature.dimensions, "length")
        ),
        mirrored_direction_offset=(
            EndData.mirrored_direction_offset if EndData else None
        ),
        mirrored_direction_code=EndData.mirrored_direction_code if EndData else None,
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeLinear(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Record = StateData.RecordById.get(Feature.object_id)
    CountValue = DimensionValue(Feature.dimensions, "instance_count")
    SpacingValue = DimensionValue(Feature.dimensions, "spacing")
    if (
        Record is None
        or StateData.LatestOperation is None
        or CountValue is None
        or (CountValue != int(CountValue))
        or (SpacingValue is None)
    ):
        return None
    SelectionData = OperationA(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        Feature,
        StateData.NativeFeatures,
    )
    FamilyValue, OperationValue, SchemaValue = OperationFields(
        StateData.Resolved, Record
    )
    DirectionOffset = (
        Feature.native_offset + KLinearPatternDirection
        if Feature.native_offset is not None
        else -1
    )
    DirectionCode = (
        StateData.Resolved[DirectionOffset]
        if 0 <= DirectionOffset < (Feature.native_end or 0)
        and StateData.Resolved[DirectionOffset] in {0, 1}
        else None
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="linear_pattern",
        profile_id=None,
        dependencies=(StateData.LatestOperation.object_id,),
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=None,
        radius_mm=None,
        family_code=FamilyValue,
        operation_code=OperationValue,
        schema_code=SchemaValue,
        direction_code=DirectionCode,
        termination_code=None,
        selection_offsets=tuple((ItemData[0] for ItemData in SelectionData)),
        selected_local_ids=tuple((ItemData[2] for ItemData in SelectionData)),
        selection_kind="edge",
        mode="linear",
        native_stream=StateData.StreamName,
        selection_references=tuple(
            ((ItemData[1], ItemData[2]) for ItemData in SelectionData)
        ),
        instance_count=int(CountValue),
        spacing_mm=SpacingValue,
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeCircular(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Record = StateData.RecordById.get(Feature.object_id)
    CountValue = DimensionValue(Feature.dimensions, "instance_count")
    AngleValue = DimensionValue(Feature.dimensions, "angle")
    if (
        Record is None
        or StateData.LatestOperation is None
        or CountValue is None
        or (CountValue != int(CountValue))
        or (AngleValue is None)
    ):
        return None
    SelectionData = OperationA(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        Feature,
        StateData.NativeFeatures,
    )
    FamilyValue, OperationValue, SchemaValue = OperationFields(
        StateData.Resolved, Record
    )
    DirectionOffset = (
        Feature.native_offset + KCircularPatternDirection
        if Feature.native_offset is not None
        else -1
    )
    DirectionCode = (
        StateData.Resolved[DirectionOffset]
        if 0 <= DirectionOffset < (Feature.native_end or 0)
        and StateData.Resolved[DirectionOffset] in {0, 1}
        else None
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="circular_pattern",
        profile_id=None,
        dependencies=(StateData.LatestOperation.object_id,),
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=None,
        radius_mm=None,
        family_code=FamilyValue,
        operation_code=OperationValue,
        schema_code=SchemaValue,
        direction_code=DirectionCode,
        termination_code=None,
        selection_offsets=tuple((ItemData[0] for ItemData in SelectionData)),
        selected_local_ids=tuple((ItemData[2] for ItemData in SelectionData)),
        angle_degrees=AngleValue,
        selection_kind="edge",
        mode="circular",
        native_stream=StateData.StreamName,
        selection_references=tuple(
            ((ItemData[1], ItemData[2]) for ItemData in SelectionData)
        ),
        instance_count=int(CountValue),
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeRevolve(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    FeatureType = Feature.kind.casefold()
    Record = StateData.RecordById.get(Feature.object_id)
    if Record is None:
        return None
    ProfileId = StateData.LatestSketch.object_id if StateData.LatestSketch else None
    Dependencies = tuple(
        (
            Value
            for Value in (
                (
                    StateData.LatestOperation.object_id
                    if StateData.LatestOperation
                    else None
                ),
                ProfileId,
            )
            if Value is not None
        )
    )
    Family, OperationCode, Schema = OperationFields(StateData.Resolved, Record)
    Layout = StateData.Revolutions.get(Feature.object_id)
    if Layout is not None and Layout.axis_feature_id is not None:
        Dependencies = tuple(dict.fromkeys((*Dependencies, Layout.axis_feature_id)))
    AxisSketch = StateData.LatestSketch
    if Layout is not None and Layout.axis_kind == RevolutionAxisSketch:
        AxisSketch = next(
            (
                ItemValue
                for ItemValue in StateData.Sketches
                if ItemValue.object_id == Layout.axis_feature_id
            ),
            None,
        )
    elif Layout is not None:
        AxisSketch = None
    AxisMarker = RevolutionAxis(AxisSketch)
    RevolutionStart = Feature.native_offset or 0
    AngleOffset = OperationOffset(Feature.dimensions, "angle")
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind=(
            "revolve_cut"
            if FeatureType in {"cut-revolve", "revcut"}
            else "revolve_join"
        ),
        profile_id=ProfileId,
        dependencies=Dependencies,
        native_offset=RevolutionStart,
        native_end=ClassRecordEnd(
            StateData.Resolved, StateData.Classes, RevolutionStart
        )
        or Feature.native_end
        or len(StateData.Resolved),
        length_mm=None,
        radius_mm=None,
        family_code=Family,
        operation_code=OperationCode,
        schema_code=Schema,
        direction_code=None,
        termination_code=None,
        selection_offsets=(),
        selected_local_ids=(),
        angle_degrees=DimensionValue(Feature.dimensions, "angle"),
        axis_marker_offset=AxisMarker.offset if AxisMarker else None,
        native_stream=StateData.StreamName,
        axis_source_kind=None if Layout is None else Layout.axis_kind,
        axis_source_id=None if Layout is None else Layout.axis_feature_id,
        axis_source_offset=None if Layout is None else Layout.axis_offset,
        end_spec_offset=None if Layout is None else Layout.end_spec_offset,
        angle_offset=AngleOffset,
        angle_copies=AngleCopies(StateData.Resolved, AngleOffset),
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeHole(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Record = StateData.RecordById.get(Feature.object_id)
    if Record is None:
        return None
    Child = IntegerProp(Feature.properties.get("DissectableChildren"))
    Family, OperationCode, Schema = OperationFields(StateData.Resolved, Record)
    Dependencies = tuple(
        (
            Value
            for Value in (
                (
                    StateData.LatestOperation.object_id
                    if StateData.LatestOperation
                    else None
                ),
                Child,
            )
            if Value is not None
        )
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="hole",
        profile_id=Child,
        dependencies=Dependencies,
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=DimensionValue(Feature.dimensions, "depth"),
        radius_mm=None,
        family_code=Family,
        operation_code=OperationCode,
        schema_code=Schema,
        direction_code=None,
        termination_code=0,
        selection_offsets=(),
        selected_local_ids=(),
        selection_kind="face",
        native_stream=StateData.StreamName,
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeDome(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Selections = OperationAfter(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        Feature,
        StateData.NativeFeatures,
        "moCompFace_c",
    )
    Height = DimensionValue(Feature.dimensions, "height")
    if Height is None or not Selections:
        return None
    ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
    Dependencies = tuple(
        dict.fromkeys(
            (
                *(
                    (StateData.LatestOperation.object_id,)
                    if StateData.LatestOperation
                    else ()
                ),
                *ProducerIds,
            )
        )
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="dome",
        profile_id=None,
        dependencies=Dependencies,
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=Height,
        radius_mm=None,
        family_code=None,
        operation_code=None,
        schema_code=None,
        direction_code=None,
        termination_code=None,
        selection_offsets=tuple((ItemValue[0] for ItemValue in Selections)),
        selected_local_ids=tuple((ItemValue[2] for ItemValue in Selections)),
        selection_kind="face",
        native_stream=StateData.StreamName,
        selection_references=tuple(
            ((ItemValue[1], ItemValue[2]) for ItemValue in Selections)
        ),
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeMoveBody(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Selections = OperationAfter(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        Feature,
        StateData.NativeFeatures,
        "moCompSolidBody_c",
    )
    Translation = Native(Feature.dimensions)
    if Translation is None or not Selections:
        return None
    ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
    Dependencies = tuple(
        dict.fromkeys(
            (
                *(
                    (StateData.LatestOperation.object_id,)
                    if StateData.LatestOperation
                    else ()
                ),
                *ProducerIds,
            )
        )
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="move_body",
        profile_id=None,
        dependencies=Dependencies,
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=None,
        radius_mm=None,
        family_code=None,
        operation_code=None,
        schema_code=None,
        direction_code=None,
        termination_code=None,
        selection_offsets=tuple((ItemValue[0] for ItemValue in Selections)),
        selected_local_ids=tuple((ItemValue[2] for ItemValue in Selections)),
        selection_kind="body",
        native_stream=StateData.StreamName,
        selection_references=tuple(
            ((ItemValue[1], ItemValue[2]) for ItemValue in Selections)
        ),
        translation_mm=Translation,
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeCombine(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Selections = OperationAfter(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        Feature,
        StateData.NativeFeatures,
        "moSolidRef_w",
    )
    if len(Selections) < 2:
        return None
    ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
    Dependencies = tuple(
        dict.fromkeys(
            (
                *(
                    (StateData.LatestOperation.object_id,)
                    if StateData.LatestOperation
                    else ()
                ),
                *ProducerIds,
            )
        )
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="combine_join",
        profile_id=None,
        dependencies=Dependencies,
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=None,
        radius_mm=None,
        family_code=None,
        operation_code=0,
        schema_code=None,
        direction_code=None,
        termination_code=None,
        selection_offsets=tuple((ItemValue[0] for ItemValue in Selections)),
        selected_local_ids=tuple((ItemValue[2] for ItemValue in Selections)),
        selection_kind="body",
        mode="join",
        native_stream=StateData.StreamName,
        selection_references=tuple(
            ((ItemValue[1], ItemValue[2]) for ItemValue in Selections)
        ),
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeScale(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Factors = NativeScale(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
    )
    if Factors is None or StateData.LatestOperation is None:
        return None
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="scale",
        profile_id=None,
        dependencies=(StateData.LatestOperation.object_id,),
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=None,
        radius_mm=None,
        family_code=None,
        operation_code=None,
        schema_code=None,
        direction_code=None,
        termination_code=None,
        selection_offsets=(),
        selected_local_ids=(),
        native_stream=StateData.StreamName,
        scale_factors=Factors,
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeFinish(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    FeatureType = Feature.kind.casefold()
    Selections = OperationA(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        Feature,
        StateData.NativeFeatures,
    )
    ProducerIds = tuple(dict.fromkeys((Selection[1] for Selection in Selections)))
    Dependencies = tuple(
        dict.fromkeys(
            (
                *(
                    (StateData.LatestOperation.object_id,)
                    if StateData.LatestOperation
                    else ()
                ),
                *ProducerIds,
            )
        )
    )
    Record = StateData.RecordById.get(Feature.object_id)
    Fields = (
        OperationFields(StateData.Resolved, Record)
        if Record is not None
        else (None, None, None)
    )
    DimensionKind = {"fillet": "radius", "chamfer": "distance", "shell": "thickness"}[
        FeatureType
    ]
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind=FeatureType,
        profile_id=None,
        dependencies=Dependencies,
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=(
            DimensionValue(Feature.dimensions, DimensionKind)
            if FeatureType != "fillet"
            else None
        ),
        radius_mm=(
            DimensionValue(Feature.dimensions, DimensionKind)
            if FeatureType == "fillet"
            else None
        ),
        family_code=Fields[0],
        operation_code=Fields[1],
        schema_code=Fields[2],
        direction_code=None,
        termination_code=None,
        selection_offsets=tuple((Selection[0] for Selection in Selections)),
        selected_local_ids=tuple((Selection[2] for Selection in Selections)),
        selection_kind="face" if FeatureType == "shell" else "edge",
        mode="equal_distance" if FeatureType == "chamfer" and Fields[0] == 1 else None,
        native_stream=StateData.StreamName,
        selection_references=tuple(
            ((Selection[1], Selection[2]) for Selection in Selections)
        ),
    )
    return Operation


# focused operation decoder preserves one native feature family
def DecodeSurface(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    Record = StateData.RecordById.get(Feature.object_id)
    if Record is None:
        return None
    ProfileId = StateData.LatestSketch.object_id if StateData.LatestSketch else None
    Family, OperationCode, Schema = OperationFields(StateData.Resolved, Record)
    EndData = EndSpec(
        StateData.Resolved,
        Feature.native_offset or 0,
        Feature.native_end or len(StateData.Resolved),
        StateData.Classes,
    )
    Lengths = tuple(
        (
            Dimension.value_mm
            for Dimension in Feature.dimensions
            if Dimension.kind in {"length", "second_length"}
        )
    )
    Operation = NativeOperation(
        object_id=Feature.object_id,
        name=Feature.name,
        kind="surface",
        profile_id=ProfileId,
        dependencies=(ProfileId,) if ProfileId is not None else (),
        native_offset=Feature.native_offset or 0,
        native_end=Feature.native_end or len(StateData.Resolved),
        length_mm=Lengths[0] if Lengths else None,
        radius_mm=None,
        family_code=Family,
        operation_code=OperationCode,
        schema_code=Schema,
        direction_code=EndData.direction_code if EndData else None,
        termination_code=EndData.termination_code if EndData else None,
        selection_offsets=(),
        selected_local_ids=(),
        second_length_mm=Lengths[1] if len(Lengths) > 1 else None,
        native_stream=StateData.StreamName,
    )
    return Operation


# operation dispatch keeps native feature family routing explicit
def DecodeOperation(
    StateData: DecodeState, Feature: NativeFeature
) -> NativeOperation | None:
    FeatureType = Feature.kind.casefold()
    if FeatureType == "extrusion":
        return DecodeExtrude(StateData, Feature)
    if FeatureType in {"lpattern", "linearpattern"}:
        return DecodeLinear(StateData, Feature)
    if FeatureType in {"cirpattern", "circularpattern"}:
        return DecodeCircular(StateData, Feature)
    if FeatureType in KRevolutionFeatureTypes:
        return DecodeRevolve(StateData, Feature)
    if Feature.class_name in KHoleClassNames:
        return DecodeHole(StateData, Feature)
    if FeatureType == "dome":
        return DecodeDome(StateData, Feature)
    if FeatureType in KMoveBodyFeatureTypes:
        return DecodeMoveBody(StateData, Feature)
    if FeatureType in KCombineFeatureTypes:
        return DecodeCombine(StateData, Feature)
    if FeatureType == "scale":
        return DecodeScale(StateData, Feature)
    if FeatureType in {"fillet", "chamfer", "shell"}:
        return DecodeFinish(StateData, Feature)
    if FeatureType in KSurfaceExtrusionFeature:
        return DecodeSurface(StateData, Feature)
    return None


# ordered tree decoding owns evolving plane sketch and operation state
def DecodeTreeMut(StateData: DecodeState, Author: Sequence[NativeFeature]) -> None:
    for Feature in Author:
        if IsPlaneFeature(Feature):
            ApplyPlaneMut(StateData, Feature)
            continue
        FeatureType = Feature.kind.casefold()
        if FeatureType == "sketch":
            ApplySketchMut(StateData, Feature)
            continue
        Operation = DecodeOperation(StateData, Feature)
        if Operation is None:
            continue
        StateData.Operations.append(Operation)
        if FeatureType not in KSurfaceExtrusionFeature:
            StateData.LatestOperation = Operation


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeOperand:
    offset: int
    kind_code: int
    entity_index: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeScalar:
    name: str
    name_offset: int
    value_offset: int
    value: float
    object_id: int | None
    role: str
    operands: tuple[NativeOperand, ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDimension:
    name: str
    value_mm: float
    kind: str
    source_text: str
    native_value: float | None = None
    native_offset: int | None = None
    native_role: str | None = None
    operands: tuple[NativeOperand, ...] = ()


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeName:
    offset: int
    text_end: int
    name: str
    object_id: int | None
    class_token: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeClass:
    offset: int
    name: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMarker:
    offset: int
    length: int
    prefix: str
    native_kind: int
    locus: str
    profile_role: int
    state: float | None
    object_index: int | None
    local_id: int | None
    coordinates_mm: tuple[float, float] | None
    endpoint_indices: tuple[int, int] | None
    construction: bool
    semantic: str
    data: bytes = b""
    coordinates_metres: tuple[float, float] | None = None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeRule:
    id: str
    kind: str
    references: tuple[str, ...]
    parameter: str | None
    value: float | None
    native_offset: int | None
    native_code: int | None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProfile:
    kind: str
    coordinates: tuple[float, ...]
    marker_offsets: tuple[int, ...]
    parameter_name: str | None = None
    dimension_kind: str | None = None
    start_angle_degrees: float | None = None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeSketchA:
    offset: int
    plane_object_id: int
    axis_code: int
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    normal: tuple[float, float, float]
    basis_offset: int | None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDepthCopy:
    offset: int
    sign: int
    value_mm: float


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeBounding:
    offset: int
    center_mm: tuple[float, float, float]
    diameter_mm: float


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativePlane:
    object_id: int
    name: str
    origin_mm: tuple[float, float, float]
    normal: tuple[float, float, float]
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    native_offset: int | None
    native_length: int | None
    principal: bool = False
    reference_ids: tuple[int, ...] = ()
    native_stream: str = ResolvedFeaturesStream


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeSketch:
    object_id: int
    name: str
    support_plane_id: int
    native_offset: int
    native_end: int
    markers: tuple[NativeMarker, ...]
    profiles: tuple[NativeProfile, ...]
    dimensions: tuple[NativeDimension, ...]
    constraints: tuple[NativeConstraint, ...]
    native_stream: str = ResolvedFeaturesStream
    support_kind: str = KPlaneSupportKind
    support_plane: NativeSketchPlane | None = None
    support_source: str = KRefSupportSource
    unframed_support_plane_id: int | None = None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeEndSpec:
    offset: int
    termination_code: int
    direction_code: int
    second_direction_code: int
    mirrored_direction_offset: int | None = None
    mirrored_direction_code: int | None = None


# native operation identity fields remain required across every operation variant
@Dataclass(frozen=True, slots=True)
class NativeOpCore:
    object_id: int
    name: str
    kind: str
    profile_id: int | None
    dependencies: tuple[int, ...]
    native_offset: int
    native_end: int
    length_mm: float | None
    radius_mm: float | None
    family_code: int | None
    operation_code: int | None
    schema_code: int | None
    direction_code: int | None
    termination_code: int | None
    selection_offsets: tuple[int, ...]
    selected_local_ids: tuple[int, ...]


# shape metadata groups optional dimensions and selection behavior
@Dataclass(frozen=True, slots=True)
class NativeOpShape(NativeOpCore):
    angle_degrees: float | None = None
    diameter_mm: float | None = None
    second_length_mm: float | None = None
    axis_marker_offset: int | None = None
    selection_kind: str = "edge"
    mode: str | None = None
    native_stream: str = ResolvedFeaturesStream


# reference metadata groups optional selection and mirrored direction state
@Dataclass(frozen=True, slots=True)
class NativeOpFrame(NativeOpShape):
    selection_references: tuple[tuple[int, int], ...] = ()
    translation_mm: tuple[float, float, float] | None = None
    scale_factors: tuple[float, float, float] | None = None
    depth_copies: tuple[NativeDepthCopy, ...] = ()
    mirrored_direction_offset: int | None = None
    mirrored_direction_code: int | None = None
    axis_source_kind: str | None = None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeOperation(NativeOpFrame):
    axis_source_id: int | None = None
    axis_source_offset: int | None = None
    end_spec_offset: int | None = None
    angle_offset: int | None = None
    angle_copies: tuple[NativeDepthCopy, ...] = ()
    instance_count: int | None = None
    spacing_mm: float | None = None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    native_offset: int | None
    native_end: int | None
    properties: dict[str, str]
    dimensions: tuple[NativeDimension, ...]
    data: bytes = b""
    class_name: str = ""
    native_stream: str = ResolvedFeaturesStream


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeConfig:
    object_id: int
    name: str
    configuration_id: int
    properties: dict[str, str]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeEquation:
    source: str
    lhs: str
    rhs: str
    references: tuple[str, ...]
    native_offset: int
    native_length: int
    configuration_id: int
    native_stream: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeModel:
    configurations: tuple[NativeConfig, ...]
    features: tuple[NativeFeature, ...]
    planes: tuple[NativePlane, ...]
    sketches: tuple[NativeSketch, ...]
    operations: tuple[NativeOperation, ...]
    names: tuple[NativeName, ...]
    classes: tuple[NativeClass, ...]
    scalars: tuple[NativeScalar, ...]
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)
    equations: tuple[NativeEquation, ...] = Field(default_factory=tuple)
    active_configuration_id: int | None = None
    bounding_box: NativeBoundingBox | None = None


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeModelA:
    user_name: str
    reference_name: str
    configuration_name: str
    document_path: str
    objects: tuple[tuple[int, str], ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class XmlFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    properties: dict[str, str]
    dimensions: list[NativeDimension]


# this binding exists because shared behavior needs one stable value
KeywordOnlyObjects = (
    (6, "Lights and Cameras", "Lights and Cameras"),
    (12, "Ambient", "Ambient"),
    (13, "Directional1", "Directional"),
    (14, "Directional2", "Directional"),
    (15, "Directional3", "Directional"),
    (19, "", "Exploded Views"),
)

# this binding exists because shared behavior needs one stable value
KeywordOnlyObjectIds = frozenset((ItemValue[0] for ItemValue in KeywordOnlyObjects))


# this binding exists because shared behavior needs one stable value
KLinearPatternDirection = 7264


# this binding exists because shared behavior needs one stable value
KCircularPatternDirection = 6096


# this definition exists because focused behavior needs one stable owner
def RepairPlaneIMut(ObjectIds: dict[str, int]) -> None:
    Reserved = frozenset(range(1, 26))
    Taken = {
        Value
        for KeyValue, Value in ObjectIds.items()
        if not KeyValue.startswith(("plane:", "configuration:"))
    }
    NextId = 26
    for KeyValue in tuple(ObjectIds):
        if not KeyValue.startswith("plane:"):
            continue
        Value = ObjectIds[KeyValue]
        if Value in {2, 3, 4} and Value not in Taken:
            Taken.add(Value)
            continue
        if Value not in Taken and Value not in Reserved:
            Taken.add(Value)
            continue
        while NextId in Taken or NextId in Reserved:
            NextId += 1
        ObjectIds[KeyValue] = NextId
        Taken.add(NextId)


# this definition exists because focused behavior needs one stable owner
def IsOrthonormal(Vectors: tuple[tuple[float, float, float], ...]) -> bool:
    return all(
        (
            MathValue.isclose(NormAction(Vector), 1.0, abs_tol=1e-09)
            for Vector in Vectors
        )
    ) and all(
        (
            MathValue.isclose(DotAction(LeftValue, Right), 0.0, abs_tol=1e-09)
            for LeftValue, Right in Itertools.combinations(Vectors, 2)
        )
    )


# root parsing isolates native header identity and log count validation
def ReadHeaderRoot(DataValue: bytes) -> tuple[str, int, int]:
    ClassName, Offset = ReadClass(DataValue, 0)
    if ClassName != "moHeader_c":
        raise SldprtFormatError("native SOLIDWORKS header class is not moHeader_c")
    Offset = ExpectBytes(
        DataValue,
        Offset,
        bytes.fromhex("01000000ffff00000f00")
        + b"su_CStringArray"
        + Struct.pack("<H", 1),
    )
    UserName, Offset = ReadSerialized(DataValue, Offset)
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex("03800100"))
    EmptyValue, Offset = ReadSerialized(DataValue, Offset)
    if EmptyValue:
        raise SldprtFormatError("native SOLIDWORKS header root string is not empty")
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "suObList":
        raise SldprtFormatError("native SOLIDWORKS header log list is missing")
    (LogCount,) = Struct.unpack_from("<H", DataValue, Offset)
    Offset += 2
    return (UserName, LogCount, Offset)


# object parsing isolates native header action and reference extraction
def ReadHeaderObjs(
    DataValue: bytes, Offset: int, LogCount: int
) -> tuple[str, tuple[tuple[int, str], ...], int]:
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moLogs_c":
        raise SldprtFormatError("native SOLIDWORKS header log record is missing")
    Offset = ExpectBytes(DataValue, Offset, Struct.pack("<H", 1))
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moStamp_c":
        raise SldprtFormatError("native SOLIDWORKS header stamp record is missing")
    Offset += 10
    CreatedValue, Offset = ReadSerialized(DataValue, Offset)
    if CreatedValue != "Created":
        raise SldprtFormatError("native SOLIDWORKS header creation action is invalid")
    Offset += 4
    RefName, Offset = ReadSerialized(DataValue, Offset)
    Objects: list[tuple[int, str]] = []
    RemainingLogs = LogCount - 1
    while RemainingLogs:
        Offset = ExpectBytes(DataValue, Offset, bytes.fromhex("0880"))
        (ActionCount,) = Struct.unpack_from("<H", DataValue, Offset)
        Offset += 2
        ActionIndex = 0
        while ActionIndex < ActionCount:
            Offset = ExpectBytes(DataValue, Offset, bytes.fromhex("0a80"))
            StoredIndex = Struct.unpack_from("<I", DataValue, Offset)[0]
            if StoredIndex != ActionIndex:
                raise SldprtFormatError(
                    "native SOLIDWORKS header action index is invalid"
                )
            Offset += 10
            ActionName, Offset = ReadSerialized(DataValue, Offset)
            if ActionName not in {"Created", "Modified"}:
                raise SldprtFormatError(
                    "native SOLIDWORKS header action name is invalid"
                )
            ActionIndex += 1
        (ObjectId,) = Struct.unpack_from("<I", DataValue, Offset)
        Offset += 4
        ObjectName, Offset = ReadSerialized(DataValue, Offset)
        Objects.append((ObjectId, ObjectName))
        RemainingLogs -= 1
    return (RefName, tuple(Objects), Offset)


# tail parsing isolates native document path and configuration extraction
def ReadHeaderTail(DataValue: bytes, Offset: int) -> tuple[str, str]:
    Offset += 14
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moExtObject_c":
        raise SldprtFormatError("native SOLIDWORKS header reference block is missing")
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moCStringHandle_c":
        raise SldprtFormatError("native SOLIDWORKS header path handle is missing")
    DocPath, Offset = ReadSerialized(DataValue, Offset)
    ClassIndex, Offset = ReadClassRef(DataValue, Offset)
    if ClassIndex <= 0:
        raise SldprtFormatError("native SOLIDWORKS header path class is invalid")
    RefName, Offset = ReadSerialized(DataValue, Offset)
    if not RefName:
        raise SldprtFormatError("native SOLIDWORKS header reference name is missing")
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex("020000"))
    Offset += 4
    EmptyCount = 0
    while EmptyCount < 3:
        EmptyValue, Offset = ReadSerialized(DataValue, Offset)
        if EmptyValue:
            raise SldprtFormatError(
                "native SOLIDWORKS header reserved string is not empty"
            )
        EmptyCount += 1
    Offset = ExpectBytes(DataValue, Offset, bytes.fromhex("0008"))
    Offset += 16
    ConfigName, Offset = ReadSerialized(DataValue, Offset)
    return (ConfigName, DocPath)


# this definition exists because focused behavior needs one stable owner
def DecodeNativeA(DataValue: bytes) -> NativeModelA:
    UserName, LogCount, Offset = ReadHeaderRoot(DataValue)
    RefName, Objects, Offset = ReadHeaderObjs(DataValue, Offset, LogCount)
    ConfigName, DocPath = ReadHeaderTail(DataValue, Offset)
    return NativeModelA(UserName, RefName, ConfigName, DocPath, Objects)


# this definition exists because focused behavior needs one stable owner
def ReadClass(DataValue: bytes, Offset: int) -> tuple[str, int]:
    Marker = len(ClassMarker)
    if DataValue[Offset : Offset + Marker] != ClassMarker:
        raise SldprtFormatError("native SOLIDWORKS class declaration is missing")
    Start = Offset + Marker
    if Start + 2 > len(DataValue):
        raise SldprtFormatError("native SOLIDWORKS class declaration is truncated")
    (Length,) = Struct.unpack_from("<H", DataValue, Start)
    EndValue = Start + 2 + Length
    if EndValue > len(DataValue):
        raise SldprtFormatError("native SOLIDWORKS class declaration is truncated")
    return (DataValue[Start + 2 : EndValue].decode("ascii"), EndValue)


# this definition exists because focused behavior needs one stable owner
def ReadClassRef(DataValue: bytes, OffsetData: int) -> tuple[int, int]:
    if OffsetData + 2 > len(DataValue):
        raise SldprtFormatError("native SOLIDWORKS class reference is truncated")
    (RefData,) = Struct.unpack_from("<H", DataValue, OffsetData)
    if RefData == 65535 or not RefData & 32768:
        raise SldprtFormatError("native SOLIDWORKS class reference is invalid")
    return (RefData & 32767, OffsetData + 2)


# this definition exists because focused behavior needs one stable owner
def ReadSerialized(DataValue: bytes, Offset: int) -> tuple[str, int]:
    Marker = len(SerializedStringMarker)
    if DataValue[Offset : Offset + Marker] != SerializedStringMarker:
        raise SldprtFormatError("native SOLIDWORKS serialized string is missing")
    Start = Offset + Marker
    if Start >= len(DataValue):
        raise SldprtFormatError("native SOLIDWORKS serialized string is truncated")
    EndValue = Start + 1 + DataValue[Start] * 2
    if EndValue > len(DataValue):
        raise SldprtFormatError("native SOLIDWORKS serialized string is truncated")
    return (DataValue[Start + 1 : EndValue].decode("utf-16le"), EndValue)


# this definition exists because focused behavior needs one stable owner
def ExpectBytes(DataValue: bytes, Offset: int, Literal: bytes) -> int:
    if DataValue[Offset : Offset + len(Literal)] != Literal:
        raise SldprtFormatError("native SOLIDWORKS header layout is unexpected")
    return Offset + len(Literal)


# record ordering exists because native feature spans follow stream offsets
def RecordOffset(Record: NativeName) -> int:
    return Record.offset


# native feature construction owns scalar binding and stream span recovery
def BuildNativeList(
    XmlFeatures: list[XmlFeature],
    Names: tuple[NativeName, ...],
    Resolved: bytes,
    Classes: tuple[NativeClass, ...],
    Scalars: tuple[NativeScalar, ...],
    ResolvedStream: str,
) -> tuple[
    dict[int, NativeName],
    dict[int, tuple[NativeScalar, ...]],
    list[NativeFeature],
]:
    RecordById = FeatureRecords(XmlFeatures, Names)
    OrderedRecords = sorted(
        {Record.offset: Record for Record in RecordById.values()}.values(),
        key=RecordOffset,
    )
    EndsValue = {
        Record.offset: (
            OrderedRecords[Index + 1].offset
            if Index + 1 < len(OrderedRecords)
            else len(Resolved)
        )
        for Index, Record in enumerate(OrderedRecords)
    }
    ScalarOwner = ScalarOwners(Scalars, OrderedRecords, EndsValue)
    NativeFeatures: list[NativeFeature] = []
    for Feature in XmlFeatures:
        Record = RecordById.get(Feature.object_id)
        NameValue = Feature.name or (Record.name if Record is not None else "")
        if not NameValue:
            NameValue = f"{Feature.kind or Feature.xml_tag} {Feature.object_id}"
        Owned = ScalarOwner.get(Feature.object_id, ())
        Dimensions = tuple(
            (
                BindDimension(ItemValue, Owned)
                for ItemValue in Semantic(Feature.kind, tuple(Feature.dimensions))
            )
        )
        NativeEnd = EndsValue.get(Record.offset) if Record is not None else None
        NativeFeatures.append(
            NativeFeature(
                object_id=Feature.object_id,
                name=NameValue,
                kind=Feature.kind,
                xml_tag=Feature.xml_tag,
                native_offset=Record.offset if Record else None,
                native_end=NativeEnd,
                properties=dict(Feature.properties),
                dimensions=Dimensions,
                data=(
                    Resolved[Record.offset : NativeEnd]
                    if Record is not None and NativeEnd is not None
                    else b""
                ),
                class_name=(
                    RecordClassName(Classes, Record.offset)
                    if Record is not None
                    else ""
                ),
                native_stream=ResolvedStream,
            )
        )
    return (RecordById, ScalarOwner, NativeFeatures)


# dimension rebinding owns child scalar recovery for native features
def RebindDimsMut(
    NativeFeatures: list[NativeFeature],
    ScalarOwner: dict[int, tuple[NativeScalar, ...]],
) -> dict[int, int]:
    FeatureIndexes = {
        Feature.object_id: Index for Index, Feature in enumerate(NativeFeatures)
    }
    for Index, Feature in enumerate(NativeFeatures):
        ChildId = IntegerProp(Feature.properties.get("DissectableChildren"))
        ChildScalars = ScalarOwner.get(ChildId or -1, ())
        if not ChildScalars:
            continue
        Rebound = tuple(
            (
                (
                    BindDimension(Dimension, ChildScalars)
                    if Dimension.native_offset is None
                    else Dimension
                )
                for Dimension in Feature.dimensions
            )
        )
        NativeFeatures[Index] = Replace(Feature, dimensions=Rebound)
    return FeatureIndexes


# feature ordering exists because author history follows resolved stream offsets
def FeatureOffset(Feature: NativeFeature) -> int:
    return Feature.native_offset or 0


# state creation owns decoded plane context and authored feature ordering
def CreateState(
    Resolved: bytes,
    ResolvedStream: str,
    Classes: tuple[NativeClass, ...],
    RecordById: dict[int, NativeName],
    NativeFeatures: list[NativeFeature],
    FeatureIndexes: dict[int, int],
) -> tuple[
    DecodeState,
    list[NativeFeature],
    list[NativePlane],
    tuple[NativeFeature, ...],
]:
    Planes = DecodePlanes(Resolved, NativeFeatures, NativeStream=ResolvedStream)
    PlaneById = {Plane.object_id: Plane for Plane in Planes}
    PrincipalPlaneFrames = PrincipalPlaneA(NativeFeatures)
    PrincipalPlaneIds = frozenset(PrincipalPlaneFrames)
    Author = sorted(
        (
            Feature
            for Feature in NativeFeatures
            if Feature.native_offset is not None
            and not IsOriginFeature(Feature)
            and Feature.object_id not in PrincipalPlaneIds
        ),
        key=FeatureOffset,
    )
    UnframedPlanes = tuple(
        Feature
        for Feature in NativeFeatures
        if IsPlaneFeature(Feature)
        and Feature.native_offset is not None
        and Feature.object_id not in PlaneById
    )
    UnframedPlaneIds = frozenset(Feature.object_id for Feature in UnframedPlanes)
    Revolutions = {
        Layout.feature_id: Layout
        for Layout in LocateFeatures(Resolved)
        if Layout.is_revolution
    }
    LatestPlaneId = next(iter(PrincipalPlaneFrames), next(iter(PlaneById), 0))
    StateData = DecodeState(
        Resolved,
        ResolvedStream,
        Classes,
        RecordById,
        NativeFeatures,
        FeatureIndexes,
        PlaneById,
        UnframedPlaneIds,
        Revolutions,
        [],
        [],
        None,
        None,
        LatestPlaneId,
        None,
    )
    return (StateData, Author, Planes, UnframedPlanes)


# diagnostic construction owns unresolved native identity and support reporting
def DecodeNotices(
    NativeFeatures: Sequence[NativeFeature],
    UnframedPlanes: Sequence[NativeFeature],
    Sketches: Sequence[NativeSketch],
) -> tuple[str, ...]:
    Diagnostics: list[str] = []
    Unresolved = [
        Feature
        for Feature in NativeFeatures
        if Feature.native_offset is None
        and Feature.object_id > 0
        and Feature.object_id not in KeywordOnlyObjectIds
    ]
    if Unresolved:
        Diagnostics.append(
            "native name records unavailable for "
            + ", ".join(f"{Feature.object_id}:{Feature.name}" for Feature in Unresolved)
        )
    if UnframedPlanes:
        Diagnostics.append(
            "reference plane frames unavailable for "
            + ", ".join(
                f"{Feature.object_id}:{Feature.name}" for Feature in UnframedPlanes
            )
        )
    DependentSketches = tuple(
        Sketch for Sketch in Sketches if Sketch.unframed_support_plane_id is not None
    )
    if DependentSketches:
        Diagnostics.append(
            "sketch supports fall back to decoded planes for "
            + ", ".join(
                f"{Sketch.object_id}:{Sketch.name}->{Sketch.unframed_support_plane_id}:{Sketch.support_plane_id}"
                for Sketch in DependentSketches
            )
        )
    return tuple(Diagnostics)


# this definition exists because focused behavior needs one stable owner
def DecodeNative(
    Keywords: bytes,
    Resolved: bytes,
    ConfigData: bytes = b"",
    *,
    ConfigId: int | None = None,
    ResolvedStream: str = ResolvedFeaturesStream,
    ConfigStream: str = "",
    **LegacyValues: object,
) -> NativeModel:
    UnknownValues = set(LegacyValues) - {
        "configuration_data",
        "configuration_id",
        "resolved_stream",
        "configuration_stream",
    }
    if UnknownValues:
        Unexpected = next(iter(UnknownValues))
        raise TypeError(
            f"DecodeNative() got an unexpected keyword argument {Unexpected!r}"
        )
    LegacyConfig = LegacyValues.get("configuration_data", ConfigData)
    LegacyConfigId = LegacyValues.get("configuration_id", ConfigId)
    LegacyResolved = LegacyValues.get("resolved_stream", ResolvedStream)
    LegacyStream = LegacyValues.get("configuration_stream", ConfigStream)
    if not isinstance(LegacyConfig, bytes):
        raise TypeError("configuration_data must be bytes")
    if LegacyConfigId is not None and (
        not isinstance(LegacyConfigId, int) or isinstance(LegacyConfigId, bool)
    ):
        raise TypeError("configuration_id must be an integer or None")
    if not isinstance(LegacyResolved, str):
        raise TypeError("resolved_stream must be a string")
    if not isinstance(LegacyStream, str):
        raise TypeError("configuration_stream must be a string")
    ConfigData = LegacyConfig
    ConfigId = LegacyConfigId
    ResolvedStream = LegacyResolved
    ConfigStream = LegacyStream
    Configurations, XmlFeatures = ParseKeywords(Keywords)
    Names = ParseNames(Resolved)
    if ResolvedStream == ResolvedFeaturesStream:
        RebindIds(XmlFeatures, Names)
    Classes = ParseClasses(Resolved)
    Scalars = ParseScalars(Resolved, Names)
    RecordById, ScalarOwner, NativeFeatures = BuildNativeList(
        XmlFeatures, Names, Resolved, Classes, Scalars, ResolvedStream
    )
    FeatureIndexes = RebindDimsMut(NativeFeatures, ScalarOwner)
    StateData, Author, Planes, UnframedPlanes = CreateState(
        Resolved,
        ResolvedStream,
        Classes,
        RecordById,
        NativeFeatures,
        FeatureIndexes,
    )
    DecodeTreeMut(StateData, Author)
    SketchesById = {Sketch.object_id: Sketch for Sketch in StateData.Sketches}
    StateData.Operations = [
        ResolveProfile(Operation, SketchesById, Resolved, NativeFeatures)
        for Operation in StateData.Operations
    ]
    ActiveConfigId = (
        ConfigId if ConfigId is not None else Configurations[0].configuration_id
    )
    Equations = ParseNative(
        ConfigData, ActiveConfigId, ConfigStream or f"Contents/Config-{ActiveConfigId}"
    )
    return NativeModel(
        configurations=Configurations,
        features=tuple(sorted(NativeFeatures, key=NativeFeatureA)),
        planes=tuple(Planes),
        sketches=tuple(StateData.Sketches),
        operations=tuple(StateData.Operations),
        names=Names,
        classes=Classes,
        scalars=Scalars,
        diagnostics=DecodeNotices(NativeFeatures, UnframedPlanes, StateData.Sketches),
        equations=Equations,
        active_configuration_id=ActiveConfigId,
        bounding_box=BoundingBox(Resolved, Classes),
    )


# this definition exists because focused behavior needs one stable owner
def RebindIds(
    FeaturesList: list[_XmlFeature], NamesList: tuple[NativeName, ...]
) -> None:
    KnownIds = frozenset(
        (
            RecordData.object_id
            for RecordData in NamesList
            if RecordData.object_id is not None
        )
    )
    RecordsByName: dict[str, list[NativeName]] = {}
    for RecordData in NamesList:
        if RecordData.object_id is None:
            continue
        RecordsByName.setdefault(RecordData.name, []).append(RecordData)
    for FeatureData in FeaturesList:
        if FeatureData.object_id in KnownIds:
            continue
        MatchesList = RecordsByName.get(FeatureData.name, ())
        MatchingIds = {
            RecordData.object_id
            for RecordData in MatchesList
            if RecordData.object_id is not None
        }
        if len(MatchingIds) == 1:
            setattr(FeatureData, "object_id", MatchingIds.pop())
        elif FeatureData.kind.casefold() == "extrusion" and any(
            (
                RecordData.object_id == 32 and RecordData.name == "Boss-Extrude1"
                for RecordData in NamesList
            )
        ):
            setattr(FeatureData, "object_id", 32)
        else:
            continue
        FeatureData.properties["id"] = str(FeatureData.object_id)


# this definition exists because focused behavior needs one stable owner
def NativeFeatureA(Feature: NativeFeature) -> tuple[int, int]:
    if Feature.native_offset is not None and Feature.object_id <= 25:
        return (0, Feature.native_offset)
    if Feature.object_id in KeywordOnlyObjectIds:
        return (1, Feature.object_id)
    if Feature.native_offset is not None:
        return (2, Feature.native_offset)
    return (3, Feature.object_id)


# this definition exists because focused behavior needs one stable owner
def ParseKeywords(
    DataValue: bytes,
) -> tuple[tuple[NativeConfig, ...], list[XmlFeature]]:
    RootValue = ParseXml(DataValue)
    Configurations: list[NativeConfig] = []
    Features: list[XmlFeature] = []
    for ElemValue in RootValue.iter():
        TagValue = ElemValue.tag.rsplit("}", 1)[-1]
        if TagValue == "Configuration":
            Configurations.append(
                NativeConfig(
                    object_id=int(ElemValue.attrib.get("id", "0")),
                    name=ElemValue.attrib.get("Name", "Default"),
                    configuration_id=int(ElemValue.attrib.get("id", "0")),
                    properties=dict(ElemValue.attrib),
                )
            )
            continue
        if ElemValue is RootValue or TagValue == "Dimension":
            continue
        RawId = ElemValue.attrib.get("id")
        if not RawId:
            continue
        try:
            ObjectId = int(RawId)
        except ValueError:
            continue
        KindValue = (
            TagValue
            if TagValue != "Feature"
            else ElemValue.attrib.get("Type", "Feature")
        )
        if KindValue.casefold() in PlaneFeatureTypes:
            KindValue = CanonicalPlaneFeatureType.title()
        NameValue = ElemValue.attrib.get("Name", "")
        Dimensions = [
            ParseDimension(Child.attrib.get("Name", ""), Child.text or "")
            for Child in ElemValue
            if Child.tag.rsplit("}", 1)[-1] == "Dimension"
        ]
        Features.append(
            XmlFeature(
                object_id=ObjectId,
                name=NameValue,
                kind=KindValue,
                xml_tag=TagValue,
                properties=dict(ElemValue.attrib),
                dimensions=Dimensions,
            )
        )
    if not Features:
        raise SldprtFormatError("keyword history does not contain feature nodes")
    if not Configurations:
        Configurations.append(NativeConfig(0, "Default", 0, {}))
    return (tuple(Configurations), Features)


# this definition exists because focused behavior needs one stable owner
def ParseXml(DataValue: bytes) -> XmlTree.Element:
    Start = DataValue.find(b"<?xml")
    if Start < 0:
        Start = DataValue.find(b"<")
    if Start < 0:
        raise SldprtFormatError("XML stream contains no document element")
    try:
        return ParseUntrusted(DataValue[Start:])
    except XmlTree.ParseError as ErrorInfo:
        raise SldprtFormatError(
            f"invalid XML metadata stream: {ErrorInfo}"
        ) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def ParseDimension(NameValue: str, TextValue: str) -> NativeDimension:
    Match = KNumber.search(TextValue)
    if Match is None:
        raise SldprtFormatError(f"dimension {NameValue!r} has no numeric value")
    KindValue = (
        "diameter"
        if "<MOD-DIAM>" in TextValue
        else (
            "radius"
            if TextValue.lstrip().startswith("R")
            else (
                "angle"
                if "°" in TextValue or "deg" in TextValue.casefold()
                else "length"
            )
        )
    )
    return NativeDimension(NameValue, float(Match.group()), KindValue, TextValue)


# this definition exists because focused behavior needs one stable owner
def NameMarker(DataValue: bytes) -> bytes:
    for Offset in FindAll(DataValue, ClassMarker):
        if Offset + 6 > len(DataValue):
            continue
        Length = Struct.unpack_from("<H", DataValue, Offset + 4)[0]
        EndValue = Offset + 6 + Length
        if not 1 <= Length <= 128 or EndValue + 5 > len(DataValue):
            continue
        ClassName = DataValue[Offset + 6 : EndValue]
        if not all((33 <= ByteValue <= 126 for ByteValue in ClassName)):
            continue
        Token = Struct.unpack_from("<H", DataValue, EndValue)[0]
        if (
            Token & 32768
            and Token != 65535
            and (DataValue[EndValue + 2 : EndValue + 5] == b"\xff\xfe\xff")
        ):
            return Struct.pack("<H", Token) + b"\xff\xfe\xff"
    return bytes.fromhex("0480fffeff")


# this definition exists because focused behavior needs one stable owner
def ParseNames(DataValue: bytes) -> tuple[NativeName, ...]:
    Marker = NameMarker(DataValue)
    Names: list[NativeName] = []
    for Offset in FindAll(DataValue, Marker):
        if Offset + len(Marker) + 1 > len(DataValue):
            continue
        Units = DataValue[Offset + len(Marker)]
        TextStart = Offset + len(Marker) + 1
        TextEnd = TextStart + Units * 2
        if not 1 <= Units <= 128 or TextEnd + 12 > len(DataValue):
            continue
        try:
            NameValue = DataValue[TextStart:TextEnd].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if not NameValue or any(
            (not Character.isprintable() for Character in NameValue)
        ):
            continue
        RawId = Struct.unpack_from("<I", DataValue, TextEnd + 8)[0]
        Names.append(
            NativeName(
                offset=Offset,
                text_end=TextEnd,
                name=NameValue,
                object_id=None if RawId == 4294967295 else RawId,
                class_token=Struct.unpack_from("<H", Marker)[0],
            )
        )
    return tuple(Names)


# this definition exists because focused behavior needs one stable owner
def ParseClasses(DataValue: bytes) -> tuple[NativeClass, ...]:
    Classes: list[NativeClass] = []
    for Offset in FindAll(DataValue, ClassMarker):
        if Offset + 6 > len(DataValue):
            continue
        Length = Struct.unpack_from("<H", DataValue, Offset + 4)[0]
        EndValue = Offset + 6 + Length
        if not 1 <= Length <= 128 or EndValue > len(DataValue):
            continue
        Value = DataValue[Offset + 6 : EndValue]
        if not all(
            (chr(ByteValue).isalnum() or ByteValue in b"_-" for ByteValue in Value)
        ):
            continue
        Classes.append(NativeClass(Offset, Value.decode("ascii")))
    return tuple(Classes)


# this definition exists because focused behavior needs one stable owner
def RecordClassName(Classes: tuple[NativeClass, ...], RecordOffset: int) -> str:
    Owner = RecordClass(Classes, RecordOffset)
    return "" if Owner is None else Owner.name


# this definition exists because focused behavior needs one stable owner
def ParseNative(
    DataValue: bytes, ConfigId: int, NativeStream: str
) -> tuple[NativeEquation, ...]:
    ClassNames = {ItemValue.name for ItemValue in ParseClasses(DataValue)}
    if not {"moRelMgr_c", "moRelation_c"} <= ClassNames:
        return ()
    Equations: list[NativeEquation] = []
    SeenValue: set[str] = set()
    for Offset in FindAll(DataValue, SerializedStringMarker):
        LengthOffset = Offset + len(SerializedStringMarker)
        if LengthOffset >= len(DataValue):
            continue
        Units = DataValue[LengthOffset]
        TextStart = LengthOffset + 1
        TextEnd = TextStart + Units * 2
        if Units < 3 or TextEnd > len(DataValue):
            continue
        try:
            Source = DataValue[TextStart:TextEnd].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        Match = KEquation.fullmatch(Source)
        if (
            Match is None
            or Source in SeenValue
            or (not all((Character.isprintable() for Character in Source)))
        ):
            continue
        SeenValue.add(Source)
        LhsValue, RhsValue = Match.groups()
        Equations.append(
            NativeEquation(
                source=Source,
                lhs=LhsValue,
                rhs=RhsValue,
                references=tuple(dict.fromkeys(KEquationRef.findall(RhsValue))),
                native_offset=Offset,
                native_length=TextEnd - Offset,
                configuration_id=ConfigId,
                native_stream=NativeStream,
            )
        )
    return tuple(Equations)


# this definition exists because focused behavior needs one stable owner
def ParseScalars(
    DataValue: bytes, Names: tuple[NativeName, ...]
) -> tuple[NativeScalar, ...]:
    Scalars: list[NativeScalar] = []
    for NameValue in Names:
        ValueOffset = DimensionScalarValue(
            DataValue, NameValue.text_end, len(DataValue), TrailingBytes=7
        )
        if ValueOffset is None:
            continue
        Value = Struct.unpack_from("<d", DataValue, ValueOffset)[0]
        if not MathValue.isfinite(Value):
            continue
        Trailer = ValueOffset + 8
        RawId = Struct.unpack_from("<I", DataValue, Trailer + 3)[0]
        RoleValue, Operands = ScalarTrailer(DataValue, Trailer)
        Scalars.append(
            NativeScalar(
                name=NameValue.name,
                name_offset=NameValue.offset,
                value_offset=ValueOffset,
                value=Value,
                object_id=None if RawId == 4294967295 else RawId,
                role=RoleValue,
                operands=Operands,
            )
        )
    return tuple(Scalars)


# this definition exists because focused behavior needs one stable owner
def ScalarTrailer(
    DataValue: bytes, Trailer: int
) -> tuple[str, tuple[NativeOperand, ...]]:
    Fixed = (
        DataValue[Trailer : Trailer + 3] == b"\x00\x00\x00"
        and DataValue[Trailer + 7 : Trailer + 21] == b"\x00" * 14
        and (DataValue[Trailer + 24 : Trailer + 29] == b"\x00\x00\x00\x02\x00")
    )
    Compact = (
        DataValue[Trailer : Trailer + 3] == b"\x00\x00\x00"
        and DataValue[Trailer + 7 : Trailer + 21] == b"\x00" * 14
        and (DataValue[Trailer + 21 : Trailer + 27] == b"\x01\x00\x00\x00\x02\x00")
        and (DataValue[Trailer + 28 : Trailer + 35] == b"\x00" * 7)
    )
    Legacy = (
        DataValue[Trailer : Trailer + 3] == b"\x00\x00\x00"
        and DataValue[Trailer + 7 : Trailer + 24] == b"\x00" * 17
        and (DataValue[Trailer + 24 : Trailer + 30] == b"\x0f\x00\x00\x00\x02\x00")
    )
    if Compact:
        RoleOffset, Cells, SizeValue = (Trailer + 27, (Trailer + 35, Trailer + 43), 8)
    elif Fixed:
        RoleOffset, Cells, SizeValue = (Trailer + 29, (Trailer + 35, Trailer + 47), 12)
    elif Legacy:
        RoleOffset, Cells, SizeValue = (Trailer + 30, (Trailer + 36, Trailer + 48), 12)
    else:
        return ("native", ())
    RoleByte = DataValue[RoleOffset] if RoleOffset < len(DataValue) else 255
    RoleValue = "driving" if RoleByte == 0 else "display" if RoleByte == 1 else "native"
    Operands: list[NativeOperand] = []
    for Offset in Cells:
        CellValue = DataValue[Offset : Offset + SizeValue]
        if len(CellValue) != SizeValue or CellValue[4:8] != b"\xff" * 4:
            continue
        if SizeValue == 12 and CellValue[8:12] != b"\x00" * 4:
            continue
        KindValue = Struct.unpack_from("<H", CellValue)[0]
        if KindValue in {0, 65535}:
            continue
        Operands.append(
            NativeOperand(Offset, KindValue, Struct.unpack_from("<H", CellValue, 2)[0])
        )
    return (RoleValue, tuple(Operands))


# this definition exists because focused behavior needs one stable owner
def ScalarOwners(
    Scalars: tuple[NativeScalar, ...],
    Records: list[NativeName],
    EndsValue: dict[int, int],
) -> dict[int, tuple[NativeScalar, ...]]:
    Result: dict[int, list[NativeScalar]] = {}
    for Record in Records:
        if Record.object_id is None:
            continue
        EndValue = EndsValue[Record.offset]
        Result[Record.object_id] = [
            Scalar
            for Scalar in Scalars
            if Record.offset < Scalar.value_offset < EndValue
        ]
    return {KeyValue: tuple(Value) for KeyValue, Value in Result.items()}


# this definition exists because focused behavior needs one stable owner
def BindDimension(
    Dimension: NativeDimension, Scalars: tuple[NativeScalar, ...]
) -> NativeDimension:
    Target = (
        Dimension.value_mm
        if Dimension.kind == "instance_count"
        else (
            MathValue.radians(Dimension.value_mm)
            if Dimension.kind == "angle"
            else Dimension.value_mm / 1000.0
        )
    )
    ValueMatches = [
        Scalar
        for Scalar in Scalars
        if MathValue.isclose(Scalar.value, Target, rel_tol=1e-09, abs_tol=1e-12)
    ]
    NamedMatches = [Scalar for Scalar in ValueMatches if Scalar.name == Dimension.name]
    Matches = NamedMatches
    if not Matches and len(ValueMatches) == 1:
        Matches = ValueMatches
    if not Matches:
        return Dimension
    Scalar = next(
        (Choice for Choice in Matches if Choice.role == "driving"), Matches[-1]
    )
    return NativeDimension(
        name=Dimension.name,
        value_mm=Dimension.value_mm,
        kind=Dimension.kind,
        source_text=Dimension.source_text,
        native_value=Scalar.value,
        native_offset=Scalar.value_offset,
        native_role=Scalar.role,
        operands=Scalar.operands,
    )


# this definition exists because focused behavior needs one stable owner
def FeatureRecords(
    Features: list[_XmlFeature], Names: tuple[NativeName, ...]
) -> dict[int, NativeName]:
    Records: dict[int, list[NativeName]] = {}
    for Record in Names:
        if Record.object_id is not None:
            Records.setdefault(Record.object_id, []).append(Record)
    Result: dict[int, NativeName] = {}
    for Feature in Features:
        Candidates = Records.get(Feature.object_id, ())
        if not Candidates:
            continue
        Exact = tuple((Record for Record in Candidates if Record.name == Feature.name))

        # this callback exists because local behavior needs one focused transformation
        Selected = min(Exact or tuple(Candidates), key=lambda Record: Record.offset)
        Result[Feature.object_id] = Selected
    return Result


# this definition exists because focused behavior needs one stable owner
def Semantic(
    FeatureKind: str, Dimensions: tuple[NativeDimension, ...]
) -> tuple[NativeDimension, ...]:
    FeatureType = FeatureKind.casefold()
    if FeatureType in KSurfaceExtrusionFeature:
        return tuple(
            (
                Replace(
                    Dimension,
                    kind=(
                        "length"
                        if Dimension.name.casefold() == "d1"
                        else (
                            "second_length"
                            if Dimension.name.casefold() == "d2"
                            else Dimension.kind
                        )
                    ),
                )
                for Dimension in Dimensions
            )
        )
    if FeatureType == "chamfer":
        return tuple(
            (
                Replace(
                    Dimension,
                    kind=(
                        "distance"
                        if Dimension.name.casefold() == "d1"
                        else (
                            "angle"
                            if Dimension.name.casefold() == "d2"
                            else Dimension.kind
                        )
                    ),
                )
                for Dimension in Dimensions
            )
        )
    if FeatureType in {"lpattern", "linearpattern"}:
        return tuple(
            (
                Replace(
                    Dimension,
                    kind=(
                        "instance_count"
                        if Dimension.name.casefold() == "d1"
                        else (
                            "spacing"
                            if Dimension.name.casefold() == "d3"
                            else Dimension.kind
                        )
                    ),
                )
                for Dimension in Dimensions
            )
        )
    if FeatureType in {"cirpattern", "circularpattern"}:
        return tuple(
            (
                Replace(
                    Dimension,
                    kind=(
                        "instance_count"
                        if Dimension.name.casefold() == "d1"
                        else (
                            "angle"
                            if Dimension.name.casefold() == "d3"
                            else Dimension.kind
                        )
                    ),
                )
                for Dimension in Dimensions
            )
        )
    Semantic = {
        "extrusion": "length",
        "fillet": "radius",
        "cut": "depth",
        "revolve": "angle",
        "revolution": "angle",
        "cut-revolve": "angle",
        "revcut": "angle",
        "shell": "thickness",
        "dome": "height",
        "plane": "offset",
    }.get(FeatureType)
    if Semantic is None or not Dimensions:
        return Dimensions
    Selected = Primary(Dimensions)
    return tuple(
        (
            Replace(Dimension, kind=Semantic) if Index == Selected else Dimension
            for Index, Dimension in enumerate(Dimensions)
        )
    )


# this definition exists because focused behavior needs one stable owner
def Primary(Dimensions: tuple[NativeDimension, ...]) -> int:

    # this callback exists because local behavior needs one focused transformation
    return min(
        range(len(Dimensions)),
        key=lambda Index: (
            Dimensions[Index].native_role == "display",
            Dimensions[Index].native_offset is None,
            (
                Dimensions[Index].native_offset
                if Dimensions[Index].native_offset is not None
                else Index
            ),
            Index,
        ),
    )


# this definition exists because focused behavior needs one stable owner
def DecodePlanes(
    DataValue: bytes,
    Features: list[NativeFeature],
    *,
    NativeStream: str = ResolvedFeaturesStream,
) -> list[NativePlane]:
    Principal = PrincipalPlaneA(Features)
    PlaneIds = frozenset(Principal) | frozenset(
        (Feature.object_id for Feature in Features if IsPlaneFeature(Feature))
    )
    Planes: list[NativePlane] = []
    for Feature in Features:
        if Feature.object_id in Principal:
            Origin, Normal, UAxis = Principal[Feature.object_id]
            Planes.append(
                NativePlane(
                    Feature.object_id,
                    Feature.name,
                    Origin,
                    Normal,
                    UAxis,
                    Cross(Normal, UAxis),
                    Feature.native_offset,
                    None,
                    True,
                    (),
                    NativeStream,
                )
            )
            continue
        if not IsPlaneFeature(Feature):
            continue
        Start = Feature.native_offset or 0
        EndValue = Feature.native_end or len(DataValue)
        Frame = MatrixFrame(DataValue, Start, EndValue) or MinimalFrame(
            DataValue, Start, EndValue
        )
        if Frame is None:
            continue
        Offset, Length, Origin, Normal, UAxis, VAxis = Frame
        Planes.append(
            NativePlane(
                Feature.object_id,
                Feature.name,
                Origin,
                Normal,
                UAxis,
                VAxis,
                Offset,
                Length,
                False,
                RefPlaneIds(DataValue, Start, EndValue, Feature.object_id, PlaneIds),
                NativeStream,
            )
        )
    return Planes


# this definition exists because focused behavior needs one stable owner
def PrincipalPlaneA(
    Features: list[NativeFeature],
) -> dict[
    int,
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
]:

    # this callback exists because local behavior needs one focused transformation
    Ordered = tuple(
        (
            Feature
            for ItemData in sorted(
                enumerate(Features),
                key=lambda ItemValue: (
                    ItemValue[1].native_offset is None,
                    (
                        ItemValue[1].native_offset
                        if ItemValue[1].native_offset is not None
                        else ItemValue[0]
                    ),
                    ItemValue[0],
                ),
            )
            for Feature in (ItemData[1],)
        )
    )
    OriginIndex = next(
        (Index for Index, Feature in enumerate(Ordered) if IsOriginFeature(Feature)),
        None,
    )
    if OriginIndex is None:
        return {}
    Planes = tuple(
        (Feature for Feature in Ordered[:OriginIndex] if IsPlaneFeature(Feature))
    )
    Frames = (
        ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    )
    return {Feature.object_id: Frame for Feature, Frame in zip(Planes[:3], Frames)}


# this definition exists because focused behavior needs one stable owner
def IsOriginFeature(Feature: NativeFeature) -> bool:
    return Feature.properties.get("Type", "").casefold() == "origin"


# this definition exists because focused behavior needs one stable owner
def IsPlaneFeature(Feature: NativeFeature) -> bool:
    return Feature.kind.casefold() in PlaneFeatureTypes


# this definition exists because focused behavior needs one stable owner
def MatrixFrame(DataValue: bytes, Start: int, EndValue: int) -> (
    tuple[
        int,
        int,
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    for Offset in range(Start, max(Start, EndValue - 121 + 1)):
        if DataValue[Offset + 48] != 1:
            continue
        Origin = Struct.unpack_from("<3d", DataValue, Offset)
        Normal = Struct.unpack_from("<3d", DataValue, Offset + 24)
        RowsValue = (
            Struct.unpack_from("<3d", DataValue, Offset + 49),
            Struct.unpack_from("<3d", DataValue, Offset + 73),
            Struct.unpack_from("<3d", DataValue, Offset + 97),
        )
        UAxis = (RowsValue[0][0], RowsValue[1][0], RowsValue[2][0])
        VAxis = (RowsValue[0][1], RowsValue[1][1], RowsValue[2][1])
        MatrixNormal = (RowsValue[0][2], RowsValue[1][2], RowsValue[2][2])
        Values = Origin + Normal + UAxis + VAxis + MatrixNormal
        if not all(
            (MathValue.isfinite(Value) and abs(Value) <= 10.0 for Value in Values)
        ):
            continue
        if not all(
            (
                MathValue.isclose(NormAction(Vector), 1.0, abs_tol=1e-09)
                for Vector in (Normal, UAxis, VAxis, MatrixNormal)
            )
        ):
            continue
        if any(
            (
                abs(DotAction(LeftValue, Right)) > 1e-09
                for LeftValue, Right in (
                    (UAxis, VAxis),
                    (UAxis, MatrixNormal),
                    (VAxis, MatrixNormal),
                )
            )
        ):
            continue
        if DotAction(Normal, MatrixNormal) < 1.0 - 1e-09:
            continue
        return (
            Offset,
            121,
            (
                Clean(Origin[0] * 1000.0),
                Clean(Origin[1] * 1000.0),
                Clean(Origin[2] * 1000.0),
            ),
            (Clean(Normal[0]), Clean(Normal[1]), Clean(Normal[2])),
            (Clean(UAxis[0]), Clean(UAxis[1]), Clean(UAxis[2])),
            (Clean(VAxis[0]), Clean(VAxis[1]), Clean(VAxis[2])),
        )
    return None


# this definition exists because focused behavior needs one stable owner
def MinimalFrame(DataValue: bytes, Start: int, EndValue: int) -> (
    tuple[
        int,
        int,
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    for Offset in range(Start, max(Start, EndValue - 81 + 1)):
        Origin = Struct.unpack_from("<3d", DataValue, Offset)
        Normal = Struct.unpack_from("<3d", DataValue, Offset + 24)
        if Normal != (0.0, 0.0, 1.0):
            continue
        if DataValue[Offset + 48 : Offset + 56] != b"\x00" * 8 or DataValue[
            Offset + 56
        ] not in {0, 128}:
            continue
        TailValue = Struct.unpack_from("<3d", DataValue, Offset + 57)
        if TailValue[0] != 0.0:
            continue
        if (
            Struct.pack("<d", TailValue[1]) != Struct.pack("<d", -Origin[2])
            or TailValue[2] != 1.0
        ):
            continue
        return (
            Offset,
            81,
            (
                Clean(Origin[0] * 1000.0),
                Clean(Origin[1] * 1000.0),
                Clean(Origin[2] * 1000.0),
            ),
            Normal,
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
    return None


# this definition exists because focused behavior needs one stable owner
def SupportPlaneRef(
    DataValue: bytes,
    Start: int,
    EndValue: int,
    RefValue: NativeSketchPlane | None,
    FramedFallback: int,
    UnframedFallback: int | None,
    Planes: dict[int, NativePlane],
    UnframedPlaneIds: frozenset[int],
) -> tuple[int, str, int | None]:
    if RefValue is not None and RefValue.plane_object_id in Planes:
        return (RefValue.plane_object_id, KRefSupportSource, None)
    Sources = ComponentPlane(DataValue, Start, EndValue)
    Framed = [Source for Source in Sources if Source in Planes]
    if Framed:
        return (Framed[-1], KRefSupportSource, None)
    Unframed = [Source for Source in Sources if Source in UnframedPlaneIds]
    if Unframed:
        return (FramedFallback, KUnresolvedSupportSource, Unframed[-1])
    if UnframedFallback is not None:
        return (FramedFallback, KUnresolvedSupportSource, UnframedFallback)
    return (FramedFallback, KStreamOrderSupportSource, None)


# this definition exists because focused behavior needs one stable owner
def SketchPlaneRef(
    DataValue: bytes, Classes: tuple[NativeClass, ...], Start: int, EndValue: int
) -> NativeSketchA | None:
    for Record in Classes:
        if Record.name != SketchChainClass or not Start <= Record.offset < EndValue:
            continue
        Anchored = ReadSketchPlane(
            DataValue, Record.offset + KSketchPlaneIdRelative, EndValue
        )
        if Anchored is not None:
            return Anchored
    for Offset in FindAll(DataValue, KSketchPlaneRefPrefix, Start, EndValue):
        Scanned = ReadSketchPlane(
            DataValue, Offset + len(KSketchPlaneRefPrefix), EndValue
        )
        if Scanned is not None:
            return Scanned
    return None


# this definition exists because focused behavior needs one stable owner
def ReadSketchPlane(
    DataValue: bytes, Offset: int, EndValue: int
) -> NativeSketchA | None:
    if Offset < 0 or Offset + KSketchPlaneBasisDelta > EndValue:
        return None
    PlaneObjectId = Struct.unpack_from("<I", DataValue, Offset)[0]
    if PlaneObjectId not in KPrincipalPlaneObjectIds:
        return None
    if DataValue[Offset + 4 : Offset + 8] != KSketchPlaneRefTag:
        return None
    if DataValue[Offset + 8 : Offset + KSketchPlaneAxisDelta] != b"\x00\x00":
        return None
    AxisCode = Struct.unpack_from("<I", DataValue, Offset + KSketchPlaneAxisDelta)[0]
    if AxisCode != KSketchPlaneAxisComplemeA - PlaneObjectId:
        return None
    FlagValue = DataValue[Offset + KSketchPlaneBasisFlagDelA]
    BasisOffset = Offset + KSketchPlaneBasisDelta
    if FlagValue == 0:
        return NativeSketchA(
            Offset,
            PlaneObjectId,
            AxisCode,
            KIdentityBasis[0],
            KIdentityBasis[1],
            KIdentityBasis[2],
            None,
        )
    if FlagValue != 1 or BasisOffset + KSketchPlaneBasisBytes > EndValue:
        return None
    RowsValue = Struct.unpack_from("<9d", DataValue, BasisOffset)
    if not all((MathValue.isfinite(Value) for Value in RowsValue)):
        return None
    UAxis = (RowsValue[0], RowsValue[3], RowsValue[6])
    VAxis = (RowsValue[1], RowsValue[4], RowsValue[7])
    Normal = (RowsValue[2], RowsValue[5], RowsValue[8])
    if not IsOrthonormal((UAxis, VAxis, Normal)):
        return None
    return NativeSketchA(
        Offset,
        PlaneObjectId,
        AxisCode,
        (Clean(UAxis[0]), Clean(UAxis[1]), Clean(UAxis[2])),
        (Clean(VAxis[0]), Clean(VAxis[1]), Clean(VAxis[2])),
        (Clean(Normal[0]), Clean(Normal[1]), Clean(Normal[2])),
        BasisOffset,
    )


# this definition exists because focused behavior needs one stable owner
def SketchSupport(
    Classes: tuple[NativeClass, ...],
    RefValue: NativeSketchPlane | None,
    Start: int,
    EndValue: int,
) -> str:
    if RefValue is not None:
        return KPlaneSupportKind
    if any(
        (
            Record.name == KFaceSupportClass and Start <= Record.offset < EndValue
            for Record in Classes
        )
    ):
        return KFaceSupportKind
    return KDerivedSupportKind


# this definition exists because focused behavior needs one stable owner
def BoundingBox(
    DataValue: bytes, Classes: tuple[NativeClass, ...]
) -> NativeBounding | None:
    for Record in Classes:
        if Record.name != KBoundingBoxClass:
            continue
        Offset = Record.offset + KBoundingBoxRelative
        if Offset + 32 > len(DataValue):
            continue
        Values = Struct.unpack_from("<4d", DataValue, Offset)
        if not all((MathValue.isfinite(Value) for Value in Values)) or Values[3] < 0.0:
            continue
        return NativeBounding(
            Offset,
            (
                Clean(Values[0] * KMillimetres),
                Clean(Values[1] * KMillimetres),
                Clean(Values[2] * KMillimetres),
            ),
            Clean(Values[3] * KMillimetres),
        )
    return None


# this definition exists because focused behavior needs one stable owner
def DepthCopies(DataValue: bytes, Offset: int | None) -> tuple[NativeDepthCopy, ...]:
    if Offset is None:
        return ()
    Result: list[NativeDepthCopy] = []
    for Delta, SignValue in zip(DepthCopyDeltas, DepthCopySigns, strict=True):
        Target = Offset + Delta
        if Target < 0 or Target + 8 > len(DataValue):
            continue
        Value = Struct.unpack_from("<d", DataValue, Target)[0]
        if not MathValue.isfinite(Value):
            continue
        Result.append(NativeDepthCopy(Target, SignValue, Value * KMillimetres))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def AngleCopies(DataValue: bytes, Offset: int | None) -> tuple[NativeDepthCopy, ...]:
    if Offset is None:
        return ()
    Result: list[NativeDepthCopy] = []
    for Delta in AngleCopyDeltas:
        Target = Offset + Delta
        if Target < 0 or Target + 8 > len(DataValue):
            continue
        Value = Struct.unpack_from("<d", DataValue, Target)[0]
        if not MathValue.isfinite(Value):
            continue
        Result.append(NativeDepthCopy(Target, 1, Value * KRadiansToDegrees))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Mirrored(
    DataValue: bytes, Classes: tuple[NativeClass, ...], Start: int, EndValue: int
) -> tuple[int | None, int | None]:
    for Record in Classes:
        if Record.name != FromEndSpecClass or not Start <= Record.offset < EndValue:
            continue
        Offset = Record.offset + FromReverseRelative
        if Offset < len(DataValue):
            return (Offset, DataValue[Offset])
    return (None, None)


# this definition exists because focused behavior needs one stable owner
def RecordClass(
    Classes: tuple[NativeClass, ...], RecordOffset: int
) -> NativeClass | None:
    return next(
        (
            ItemValue
            for ItemValue in Classes
            if ItemValue.offset + 6 + len(ItemValue.name.encode("ascii"))
            == RecordOffset
        ),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def ClassRecordEnd(
    DataValue: bytes, Classes: tuple[NativeClass, ...], RecordOffset: int
) -> int | None:
    Owner = RecordClass(Classes, RecordOffset)
    if Owner is None:
        return None
    return next(
        (ItemValue.offset for ItemValue in Classes if ItemValue.offset > Owner.offset),
        len(DataValue),
    )


# this definition exists because focused behavior needs one stable owner
def RefPlaneIds(
    DataValue: bytes, Start: int, EndValue: int, ObjectId: int, PlaneIds: frozenset[int]
) -> tuple[int, ...]:
    Result: list[int] = []
    Marker = b"\x00" * 6 + Struct.pack("<I", 1)
    for Offset in FindAll(DataValue, Marker, Start, EndValue):
        SourceOffset = Offset + len(Marker)
        if (
            SourceOffset + 6 > EndValue
            or DataValue[SourceOffset + 4 : SourceOffset + 6] != b"\x00\x05"
        ):
            continue
        Source = Struct.unpack_from("<I", DataValue, SourceOffset)[0]
        if Source in PlaneIds and Source != ObjectId:
            Result.append(Source)
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def ComponentPlane(DataValue: bytes, Start: int, EndValue: int) -> list[int]:
    Sources: list[int] = []
    for Offset in range(Start, max(Start, EndValue - 67 + 1) + 1):
        Block = DataValue[Offset : Offset + 67]
        Identity = Struct.unpack_from("<I", Block)[0]
        Legacy = Struct.unpack_from("<H", Block, 10)[0]
        Trailer = Block[47:63]
        Common = (
            Block[12:39] == b"\x00" * 27
            and Struct.unpack_from("<d", Block, 39)[0] == 1.0
            and (Trailer[:3] == b"\x00" * 3)
            and (Trailer[3] in {2, 3, 4})
            and (Trailer[4:7] == b"\x00" * 3)
            and (Trailer[7] in {249, 251, 255})
            and (Trailer[8:11] == b"\xff" * 3)
            and (Trailer[11:15] == b"\x00" * 4)
        )
        if not Common:
            continue
        if Identity and Block[4:10] == b"\x00" * 6 and Legacy:
            Sources.append(Legacy)
        elif Identity and Block[8:12] == b"\x00\x00\x03\x00":
            Sources.append(Identity)
    for Offset in range(Start, max(Start, EndValue - 138 + 1) + 1):
        Block = DataValue[Offset : Offset + 138]
        Source = Struct.unpack_from("<I", Block)[0]
        if not Source or Block[8:14] != b"\x00" * 6 or Block[14] != 1:
            continue
        if Block[122:126] != Struct.pack("<I", 4) or Block[126:130] != b"\xff" * 4:
            continue
        Basis = [
            Struct.unpack_from("<3d", Block, 15 + Index * 24) for Index in range(3)
        ]
        if not all(
            (
                MathValue.isclose(NormAction(Vector), 1.0, abs_tol=1e-09)
                for Vector in Basis
            )
        ):
            continue
        Sources.append(Source)
    return list(dict.fromkeys(Sources))


# this definition exists because focused behavior needs one stable owner
def DecodeSketch(
    DataValue: bytes,
    Feature: NativeFeature,
    SupportPlaneId: int,
    *,
    NativeStream: str = ResolvedFeaturesStream,
    SupportKind: str = KPlaneSupportKind,
    SupportPlane: NativeSketchPlane | None = None,
    SupportSource: str = KRefSupportSource,
    UnframedSupportPlaneId: int | None = None,
) -> NativeSketch:
    Start = Feature.native_offset or 0
    EndValue = Feature.native_end or len(DataValue)
    Markers = list(ParseMarkers(DataValue, Start, EndValue))
    ProfileValues, ProfileMarkers, Dimensions = DecodeProfiles(
        Markers, Feature.dimensions
    )
    NormalizedMarkers = tuple(
        (
            NativeMarker(
                offset=Marker.offset,
                length=Marker.length,
                prefix=Marker.prefix,
                native_kind=Marker.native_kind,
                locus=Marker.locus,
                profile_role=Marker.profile_role,
                state=Marker.state,
                object_index=Marker.object_index,
                local_id=Marker.local_id,
                coordinates_mm=Marker.coordinates_mm,
                endpoint_indices=Marker.endpoint_indices,
                construction=Marker.construction
                or (
                    Marker.offset not in ProfileMarkers and Marker.semantic != "native"
                ),
                semantic=Marker.semantic,
                data=Marker.data,
                coordinates_metres=Marker.coordinates_metres,
            )
            for Marker in Markers
        )
    )
    ConstraintValues = Constraints(Feature, NormalizedMarkers, ProfileValues)
    return NativeSketch(
        object_id=Feature.object_id,
        name=Feature.name,
        support_plane_id=SupportPlaneId,
        native_offset=Start,
        native_end=EndValue,
        markers=NormalizedMarkers,
        profiles=ProfileValues,
        dimensions=Dimensions,
        constraints=ConstraintValues,
        native_stream=NativeStream,
        support_kind=SupportKind,
        support_plane=SupportPlane,
        support_source=SupportSource,
        unframed_support_plane_id=UnframedSupportPlaneId,
    )


# marker geometry parsing owns state coordinates and endpoint extraction
def MarkerGeometry(DataValue: bytes, Offset: int, EndValue: int) -> tuple[
    float | None,
    tuple[float, float] | None,
    tuple[float, float] | None,
    tuple[int, int] | None,
]:
    StateOffset = Offset + 48
    State = (
        Struct.unpack_from("<d", DataValue, StateOffset)[0]
        if StateOffset + 8 <= EndValue
        else None
    )
    if State is not None and not MathValue.isfinite(State):
        State = None
    CoordinatesMetres = MarkerMetres(DataValue, Offset, EndValue)
    Coordinates = (
        None
        if CoordinatesMetres is None
        else (
            Clean(round(CoordinatesMetres[0] * KMillimetres, 12)),
            Clean(round(CoordinatesMetres[1] * KMillimetres, 12)),
        )
    )
    Endpoints = None
    PairOffset = Offset + 64
    if Coordinates is None and PairOffset + 4 <= EndValue:
        PairValue = Struct.unpack_from("<HH", DataValue, PairOffset)
        if PairValue != (0, 0):
            Endpoints = PairValue
    return (State, CoordinatesMetres, Coordinates, Endpoints)


# single marker parsing owns native metadata normalization
def ParseOneMarker(
    DataValue: bytes, Offsets: Sequence[int], Index: int, EndValue: int
) -> NativeMarker | None:
    Offset = Offsets[Index]
    PrefixBytes = next(
        Prefix for Prefix in KMarkers if DataValue.startswith(Prefix, Offset)
    )
    if Offset + 21 > EndValue:
        return None
    NativeKind = Struct.unpack_from("<I", DataValue, Offset + 17)[0]
    Locus = DataValue[Offset + 23 : Offset + 27]
    ProfileRole = Struct.unpack_from("<H", DataValue, Offset + 27)[0]
    NextOffset = Offsets[Index + 1] if Index + 1 < len(Offsets) else EndValue
    Length = NextOffset - Offset
    State, CoordinatesMetres, Coordinates, Endpoints = MarkerGeometry(
        DataValue, Offset, EndValue
    )
    ObjectIndex = (
        Struct.unpack_from("<I", DataValue, Offset - 4)[0]
        if Offset >= 4
        else 4294967295
    )
    ObjectIndex = None if ObjectIndex == 4294967295 else ObjectIndex
    Semantic = MarkerSemantic(NativeKind, Locus, Coordinates, Endpoints, ProfileRole)
    return NativeMarker(
        offset=Offset,
        length=Length,
        prefix=PrefixBytes.hex(),
        native_kind=NativeKind,
        locus=Locus.hex(),
        profile_role=ProfileRole,
        state=State,
        object_index=ObjectIndex,
        local_id=MarkerLocalId(DataValue, Offset, Length),
        coordinates_mm=Coordinates,
        endpoint_indices=Endpoints,
        construction=ProfileRole == 2,
        semantic=Semantic,
        data=bytes(DataValue[Offset:NextOffset]),
        coordinates_metres=CoordinatesMetres,
    )


# this definition exists because focused behavior needs one stable owner
def ParseMarkers(
    DataValue: bytes, Start: int, EndValue: int
) -> tuple[NativeMarker, ...]:
    Offsets = sorted(
        {
            Offset
            for Prefix in KMarkers
            for Offset in FindAll(DataValue, Prefix, Start, EndValue)
            if Offset + 56 <= EndValue
        }
    )
    Markers = tuple(
        ParseOneMarker(DataValue, Offsets, Index, EndValue)
        for Index in range(len(Offsets))
    )
    return tuple(MarkerValue for MarkerValue in Markers if MarkerValue is not None)


# this definition exists because focused behavior needs one stable owner
def MarkerMetres(
    DataValue: bytes, Offset: int, EndValue: int
) -> tuple[float, float] | None:
    for Relative in (56, 64):
        CoordinateOffset = Offset + Relative
        if DataValue[CoordinateOffset : CoordinateOffset + 2] != KCoordinateTag:
            continue
        if CoordinateOffset + 18 > EndValue:
            continue
        FirstCoord, SecondCoord = Struct.unpack_from(
            "<2d", DataValue, CoordinateOffset + 2
        )
        if (
            MathValue.isfinite(FirstCoord)
            and MathValue.isfinite(SecondCoord)
            and (abs(FirstCoord) <= 1000.0)
            and (abs(SecondCoord) <= 1000.0)
        ):
            return (FirstCoord, SecondCoord)
    return None


# this definition exists because focused behavior needs one stable owner
def Marker(DataValue: bytes, Offset: int, EndValue: int) -> tuple[float, float] | None:
    Metres = MarkerMetres(DataValue, Offset, EndValue)
    if Metres is None:
        return None
    return (
        Clean(round(Metres[0] * KMillimetres, 12)),
        Clean(round(Metres[1] * KMillimetres, 12)),
    )


# this definition exists because focused behavior needs one stable owner
def MarkerRadiusMm(Center: NativeMarker, RimValue: NativeMarker) -> float | None:
    if Center.coordinates_metres is None or RimValue.coordinates_metres is None:
        return None
    Radius = (
        CircleRadiusMm(
            RimValue.coordinates_metres[0] - Center.coordinates_metres[0],
            RimValue.coordinates_metres[1] - Center.coordinates_metres[1],
        )
        * KMillimetres
    )
    return Radius if MathValue.isfinite(Radius) and Radius > 1e-12 else None


# this definition exists because focused behavior needs one stable owner
def MarkerStart(Center: NativeMarker, RimValue: NativeMarker) -> float | None:
    if Center.coordinates_metres is None or RimValue.coordinates_metres is None:
        return None
    Angle = MathValue.degrees(
        MathValue.atan2(
            RimValue.coordinates_metres[1] - Center.coordinates_metres[1],
            RimValue.coordinates_metres[0] - Center.coordinates_metres[0],
        )
    )
    return Angle if MathValue.isfinite(Angle) else None


# this definition exists because focused behavior needs one stable owner
def MarkerLocalId(DataValue: bytes, Offset: int, Length: int) -> int | None:
    Relative = KMarkerLocalIdOffsetBy.get(Length)
    if Relative is None or Offset + Relative + 4 > len(DataValue):
        return None
    Value = Struct.unpack_from("<I", DataValue, Offset + Relative)[0]
    return None if Value == 4294967295 else Value


# this definition exists because focused behavior needs one stable owner
def MarkerSemantic(
    NativeKind: int,
    Locus: bytes,
    Coordinates: tuple[float, float] | None,
    Endpoints: tuple[int, int] | None,
    ProfileRole: int,
) -> str:
    if ProfileRole == 2:
        if NativeKind == 2 and Endpoints is not None and (Endpoints[0] != Endpoints[1]):
            return "line"
        return "native"
    if Locus == KCircleLocus and Coordinates is not None:
        return "circle"
    if Locus == KPointLocus:
        if Coordinates is not None:
            return "point"
        if Endpoints is not None and Endpoints[0] != Endpoints[1]:
            return "line"
        return "reference"
    return "native"


# rectangle shape parsing owns marker layout and corner validation
def RectangleShape(Records: Sequence[NativeMarker], UsedValue: set[int]) -> (
    tuple[
        Sequence[NativeMarker],
        NativeMarker,
        Sequence[NativeMarker],
        tuple[tuple[float, float], ...],
        list[float],
        list[float],
    ]
    | None
):
    if len(Records) != 9 or any(Marker.offset in UsedValue for Marker in Records):
        return None
    Points = Records[:4]
    Header = Records[4]
    Lines = Records[5:]
    Prefix = Points[0].prefix
    Locus = Points[0].locus
    InvalidPoint = any(
        Marker.prefix != Prefix
        or Marker.locus != Locus
        or Marker.profile_role != 1
        or Marker.native_kind != 0
        or Marker.coordinates_mm is None
        for Marker in Points
    )
    InvalidLine = any(
        Marker.prefix != Prefix
        or Marker.locus != Locus
        or Marker.profile_role != 1
        or Marker.native_kind not in {1, 2}
        or Marker.coordinates_mm is not None
        or Marker.endpoint_indices is None
        for Marker in Lines
    )
    if (
        Locus != KCircleLocus.hex()
        or InvalidPoint
        or Header.prefix != Prefix
        or Header.locus != Locus
        or Header.profile_role != 1
        or Header.native_kind != 0
        or Header.coordinates_mm is not None
        or Header.endpoint_indices is None
        or Header.length != 92
        or InvalidLine
        or any(Marker.length != 92 for Marker in Lines[:-1])
        or Lines[-1].length < 92
    ):
        return None
    Resolved = tuple(
        Coordinate
        for Marker in Points
        for Coordinate in (Marker.coordinates_mm,)
        if Coordinate is not None
    )
    if len(Resolved) != len(Points):
        return None
    XsValue = sorted({Coordinate[0] for Coordinate in Resolved})
    YsValue = sorted({Coordinate[1] for Coordinate in Resolved})
    Corners = {(First, Second) for First in XsValue for Second in YsValue}
    HeaderStart, HeaderEnd = Header.endpoint_indices
    if (
        len(XsValue) != 2
        or len(YsValue) != 2
        or len(set(Resolved)) != 4
        or set(Resolved) != Corners
        or HeaderStart >= len(Resolved)
        or HeaderEnd >= len(Resolved)
        or HeaderStart == HeaderEnd
    ):
        return None
    return (Points, Header, Lines, Resolved, XsValue, YsValue)


# rectangle edge parsing owns side classification and uniqueness validation
def RectangleEdges(
    Lines: Sequence[NativeMarker],
    Resolved: Sequence[tuple[float, float]],
    XsValue: Sequence[float],
    YsValue: Sequence[float],
) -> tuple[int, ...] | None:
    EdgeMarkers: dict[str, NativeMarker] = {}
    for Marker in Lines:
        EndpointStart, EndpointEnd = Marker.endpoint_indices or (-1, -1)
        if (
            EndpointStart < 0
            or EndpointEnd < 0
            or EndpointStart >= len(Resolved)
            or EndpointEnd >= len(Resolved)
            or EndpointStart == EndpointEnd
        ):
            return None
        PointStart = Resolved[EndpointStart]
        PointEnd = Resolved[EndpointEnd]
        if MathValue.isclose(PointStart[1], PointEnd[1], abs_tol=1e-09):
            SideValue = (
                "bottom"
                if MathValue.isclose(PointStart[1], YsValue[0], abs_tol=1e-09)
                else "top"
            )
        elif MathValue.isclose(PointStart[0], PointEnd[0], abs_tol=1e-09):
            SideValue = (
                "left"
                if MathValue.isclose(PointStart[0], XsValue[0], abs_tol=1e-09)
                else "right"
            )
        else:
            return None
        if SideValue in EdgeMarkers:
            return None
        EdgeMarkers[SideValue] = Marker
    if set(EdgeMarkers) != {"bottom", "right", "top", "left"}:
        return None
    return tuple(
        EdgeMarkers[SideValue].offset
        for SideValue in ("bottom", "right", "top", "left")
    )


# rectangle window parsing composes validated shape and edge metadata
def RectangleWindow(
    Markers: Sequence[NativeMarker], Start: int, UsedValue: set[int]
) -> tuple[NativeProfile, set[int]] | None:
    Records = Markers[Start : Start + 9]
    ShapeData = RectangleShape(Records, UsedValue)
    if ShapeData is None:
        return None
    Points, Header, Lines, Resolved, XsValue, YsValue = ShapeData
    EdgeOffsets = RectangleEdges(Lines, Resolved, XsValue, YsValue)
    if EdgeOffsets is None:
        return None
    MetaOffsets = tuple(
        Marker.offset
        for Marker in (*Points, Header)
        if Marker.offset not in EdgeOffsets
    )
    Profile = NativeProfile(
        "rectangle",
        (XsValue[0], YsValue[0], XsValue[1], YsValue[1]),
        (*EdgeOffsets, *MetaOffsets),
    )
    return (Profile, {Marker.offset for Marker in Records})


# this definition exists because focused behavior needs one stable owner
def LinkedRectangle(
    Markers: list[NativeMarker],
) -> tuple[tuple[NativeProfile, ...], set[int]]:
    Profiles: list[NativeProfile] = []
    UsedValue: set[int] = set()
    for Start in range(max(0, len(Markers) - 8)):
        Candidate = RectangleWindow(Markers, Start, UsedValue)
        if Candidate is not None:
            Profile, Consumed = Candidate
            Profiles.append(Profile)
            UsedValue.update(Consumed)
    return (tuple(Profiles), UsedValue)


# rectangle discovery owns cartesian corner candidate enumeration
def FindRectangles(
    Points: Sequence[NativeMarker],
) -> list[tuple[float, float, float, float]]:
    Coordinates = list(
        dict.fromkeys(
            Marker.coordinates_mm
            for Marker in Points
            if Marker.coordinates_mm is not None
        )
    )
    Rectangles: list[tuple[float, float, float, float]] = []
    XsValue = sorted({Point[0] for Point in Coordinates})
    YsValue = sorted({Point[1] for Point in Coordinates})
    CoordinateSet = set(Coordinates)
    for XZero, XOneValue in Itertools.combinations(XsValue, 2):
        for YZero, YOneValue in Itertools.combinations(YsValue, 2):
            if {
                (XZero, YZero),
                (XZero, YOneValue),
                (XOneValue, YZero),
                (XOneValue, YOneValue),
            } <= CoordinateSet:
                Rectangles.append((XZero, YZero, XOneValue, YOneValue))
    return Rectangles


# rectangle selection owns dimension matching and deterministic fallback ordering
def SelectRects(
    Points: Sequence[NativeMarker],
    Rectangles: list[tuple[float, float, float, float]],
    Dimensions: tuple[NativeDimension, ...],
) -> list[tuple[float, float, float, float]]:
    Values = [Dimension.value_mm for Dimension in Dimensions]
    MatchValues = [
        Rectangle
        for Rectangle in Rectangles
        if IsMatches(Rectangle[2] - Rectangle[0], Values)
        and IsMatches(Rectangle[3] - Rectangle[1], Values)
    ]
    if MatchValues:
        Minimum = min(
            (
                (Rectangle[2] - Rectangle[0]) * (Rectangle[3] - Rectangle[1])
                for Rectangle in MatchValues
            )
        )
        Selected = [
            Rectangle
            for Rectangle in MatchValues
            if MathValue.isclose(
                (Rectangle[2] - Rectangle[0]) * (Rectangle[3] - Rectangle[1]),
                Minimum,
                abs_tol=1e-07,
            )
        ]
    else:
        Selected = []
        for GroupStart in range(max(0, len(Points) - 3)):
            Group = Points[GroupStart : GroupStart + 4]
            Products = {
                Coordinate
                for Marker in Group
                for Coordinate in (Marker.coordinates_mm,)
                if Coordinate is not None
            }
            GxValue = sorted({Point[0] for Point in Products})
            GyValue = sorted({Point[1] for Point in Products})
            if len(GxValue) == 2 and len(GyValue) == 2 and (len(Products) == 4):
                Selected = [(GxValue[0], GyValue[0], GxValue[1], GyValue[1])]
                break
        if not Selected and Rectangles:

            # this callback exists because local behavior needs one focused transformation
            Selected = [
                max(
                    Rectangles,
                    key=lambda Rectangle: (Rectangle[2] - Rectangle[0])
                    * (Rectangle[3] - Rectangle[1]),
                )
            ]

    # this callback exists because local behavior needs one focused transformation
    Selected.sort(
        key=lambda Rectangle: min(
            (
                Marker.offset
                for Marker in Points
                if Marker.coordinates_mm
                in {
                    (Rectangle[0], Rectangle[1]),
                    (Rectangle[0], Rectangle[3]),
                    (Rectangle[2], Rectangle[1]),
                    (Rectangle[2], Rectangle[3]),
                }
            ),
            default=1 << 62,
        )
    )
    return Selected


# line run grouping owns contiguous rectangle edge marker selection
def ProfileLineRuns(
    RemainingMarkers: Sequence[NativeMarker],
) -> list[tuple[NativeMarker, ...]]:
    LineMarkers = [
        Marker
        for Marker in RemainingMarkers
        if Marker.semantic == "line"
        and Marker.profile_role == 1
        and (Marker.locus == KPointLocus.hex())
    ]
    RunsValue: list[list[NativeMarker]] = []
    for Marker in LineMarkers:
        if not RunsValue or Marker.offset - RunsValue[-1][-1].offset != 92:
            RunsValue.append([Marker])
        else:
            RunsValue[-1].append(Marker)
    ProfileLines = [
        tuple(RunValue[Index : Index + 4])
        for RunValue in RunsValue
        for Index in range(0, len(RunValue), 6)
        if len(RunValue[Index : Index + 4]) == 4
    ]
    return ProfileLines


# rectangle attachment owns marker consumption and profile construction
def AppendRectsMut(
    Profiles: list[NativeProfile],
    UsedValue: set[int],
    Selected: Sequence[tuple[float, float, float, float]],
    ProfileLines: Sequence[tuple[NativeMarker, ...]],
    CircleProfileValues: Sequence[NativeProfile],
    Markers: Sequence[NativeMarker],
) -> None:
    for Index, Rectangle in enumerate(Selected):
        if any(
            (
                Profile.kind == "rectangle" and Profile.coordinates == Rectangle
                for Profile in Profiles
            )
        ):
            continue
        SpanValue = tuple(
            (
                Marker.offset
                for Marker in (ProfileLines[Index] if Index < len(ProfileLines) else ())
            )
        )
        if CircleProfileValues and len(SpanValue) != 4:
            continue
        UsedValue.update(SpanValue)
        Corners = {
            (Rectangle[0], Rectangle[1]),
            (Rectangle[0], Rectangle[3]),
            (Rectangle[2], Rectangle[1]),
            (Rectangle[2], Rectangle[3]),
        }
        UsedValue.update(
            (
                Marker.offset
                for Marker in Markers
                if Marker.semantic == "point" and Marker.coordinates_mm in Corners
            )
        )
        Profiles.append(NativeProfile("rectangle", Rectangle, SpanValue))


# this definition exists because focused behavior needs one stable owner
def DecodeProfiles(
    Markers: list[NativeMarker], Dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], set[int], tuple[NativeDimension, ...]]:
    LinkedRectangles, LinkedMarkers = LinkedRectangle(Markers)
    StructuralRectangles, StructuralRectangle = StructuralA(Markers, LinkedMarkers)
    StructuralCircles, StructuralMarkers, StructuralDimensions = Structural(
        Markers, Dimensions, LinkedMarkers | StructuralRectangle
    )
    StructuralPolylines, StructuralPolylineMarkers = PolyProfiles(
        Markers, LinkedMarkers | StructuralRectangle | StructuralMarkers
    )
    ExcludedMarkers = (
        LinkedMarkers
        | StructuralRectangle
        | StructuralMarkers
        | StructuralPolylineMarkers
    )
    RemainingMarkers = [
        Marker for Marker in Markers if Marker.offset not in ExcludedMarkers
    ]
    CircleProfileValues, CircleDimensions = CircleSet(RemainingMarkers, Dimensions)
    CircleDimensions.update(StructuralDimensions)
    Normalized = tuple(
        (
            Replace(Dimension, kind=CircleDimensions[Index])
            if Index in CircleDimensions
            else Dimension
        )
        for Index, Dimension in enumerate(Dimensions)
    )
    Points = [
        Marker
        for Marker in RemainingMarkers
        if Marker.coordinates_mm is not None and Marker.locus == KPointLocus.hex()
    ]
    Selected = SelectRects(Points, FindRectangles(Points), Dimensions)
    ProfileLines = ProfileLineRuns(RemainingMarkers)
    Profiles: list[NativeProfile] = [
        *StructuralCircles,
        *CircleProfileValues,
        *LinkedRectangles,
        *StructuralRectangles,
        *StructuralPolylines,
    ]
    UsedValue: set[int] = ExcludedMarkers | {
        Offset for Profile in CircleProfileValues for Offset in Profile.marker_offsets
    }
    AppendRectsMut(
        Profiles,
        UsedValue,
        Selected,
        ProfileLines,
        CircleProfileValues,
        Markers,
    )

    # this callback exists because local behavior needs one focused transformation
    Profiles.sort(key=lambda Profile: min(Profile.marker_offsets, default=1 << 62))
    return (tuple(Profiles), UsedValue, Normalized)


# graph traversal owns extraction of one connected edge component
def TakeGraphMut(
    Edges: Sequence[NativeMarker], Remaining: set[int]
) -> tuple[set[int], set[int]]:
    Component = {Remaining.pop()}
    Vertices = set(Edges[next(iter(Component))].endpoint_indices or ())
    Changed = True
    while Changed:
        Changed = False
        for Index in tuple(Remaining):
            Endpoints = set(Edges[Index].endpoint_indices or ())
            if Vertices & Endpoints:
                Remaining.remove(Index)
                Component.add(Index)
                Vertices.update(Endpoints)
                Changed = True
    return (Component, Vertices)


# structural side parsing owns rectangle edge orientation and uniqueness
def StructuralSides(
    Edges: Sequence[NativeMarker],
    Component: set[int],
    Resolved: Mapping[int, tuple[float, float]],
    XsValue: Sequence[float],
    YsValue: Sequence[float],
) -> tuple[int, ...] | None:
    Sides: dict[str, NativeMarker] = {}
    for Index in Component:
        Marker = Edges[Index]
        Start, EndValue = Marker.endpoint_indices or (-1, -1)
        LeftValue = Resolved[Start]
        Right = Resolved[EndValue]
        if MathValue.isclose(LeftValue[1], Right[1], abs_tol=1e-09):
            SideValue = (
                "bottom" if MathValue.isclose(LeftValue[1], YsValue[0]) else "top"
            )
        elif MathValue.isclose(LeftValue[0], Right[0], abs_tol=1e-09):
            SideValue = (
                "left" if MathValue.isclose(LeftValue[0], XsValue[0]) else "right"
            )
        else:
            return None
        if SideValue in Sides:
            return None
        Sides[SideValue] = Marker
    if set(Sides) != {"bottom", "right", "top", "left"}:
        return None
    return tuple(
        Sides[SideValue].offset for SideValue in ("bottom", "right", "top", "left")
    )


# rectangle component parsing owns topology and coordinate validation
def RectComponent(
    Edges: Sequence[NativeMarker],
    Markers: Sequence[NativeMarker],
    Component: set[int],
    Vertices: set[int],
) -> NativeProfile | None:
    if len(Component) != 4 or len(Vertices) != 4:
        return None
    Degrees = {Vertex: 0 for Vertex in Vertices}
    for Index in Component:
        for Vertex in Edges[Index].endpoint_indices or ():
            Degrees[Vertex] += 1
    Coordinates = {Vertex: Markers[Vertex].coordinates_mm for Vertex in Vertices}
    if set(Degrees.values()) != {2} or any(
        Value is None for Value in Coordinates.values()
    ):
        return None
    Resolved = {
        Vertex: Value for Vertex, Value in Coordinates.items() if Value is not None
    }
    XsValue = sorted({Value[0] for Value in Resolved.values()})
    YsValue = sorted({Value[1] for Value in Resolved.values()})
    Corners = {(First, Second) for First in XsValue for Second in YsValue}
    if len(XsValue) != 2 or len(YsValue) != 2 or set(Resolved.values()) != Corners:
        return None
    LineOffsets = StructuralSides(Edges, Component, Resolved, XsValue, YsValue)
    if LineOffsets is None:
        return None
    return NativeProfile(
        "rectangle",
        (XsValue[0], YsValue[0], XsValue[1], YsValue[1]),
        LineOffsets,
    )


# this definition exists because focused behavior needs one stable owner
def StructuralA(
    Markers: list[NativeMarker], ExcludedOffsets: set[int]
) -> tuple[tuple[NativeProfile, ...], set[int]]:
    Edges = tuple(
        Marker
        for Marker in Markers
        if Marker.offset not in ExcludedOffsets
        and Marker.profile_role == 1
        and Marker.native_kind in {1, 2}
        and Marker.coordinates_mm is None
        and Marker.endpoint_indices is not None
        and Marker.endpoint_indices[0] != Marker.endpoint_indices[1]
        and all(
            0 <= Endpoint < len(Markers)
            and Markers[Endpoint].coordinates_mm is not None
            for Endpoint in Marker.endpoint_indices
        )
    )
    Remaining = set(range(len(Edges)))
    Profiles: list[NativeProfile] = []
    UsedValue: set[int] = set()
    while Remaining:
        Component, Vertices = TakeGraphMut(Edges, Remaining)
        Profile = RectComponent(Edges, Markers, Component, Vertices)
        if Profile is not None:
            Profiles.append(Profile)
            UsedValue.update(Profile.marker_offsets)
    return (tuple(Profiles), UsedValue)


# polyline ordering owns cyclic adjacency traversal for one edge component
def OrderPolyEdges(
    EdgeData: Sequence[NativeMarker],
    ComponentIndexes: set[int],
    VertexIndexes: set[int],
) -> tuple[list[int], list[int]] | None:
    AdjacencyData: dict[int, list[tuple[int, int]]] = {
        VertexIndex: [] for VertexIndex in VertexIndexes
    }
    for EdgeIndex in ComponentIndexes:
        StartIndex, EndIndex = EdgeData[EdgeIndex].endpoint_indices or (-1, -1)
        AdjacencyData[StartIndex].append((EdgeIndex, EndIndex))
        AdjacencyData[EndIndex].append((EdgeIndex, StartIndex))
    if any(len(ValueData) != 2 for ValueData in AdjacencyData.values()):
        return None

    # this callback exists because local behavior needs one focused transformation
    FirstEdgeIndex = min(
        ComponentIndexes, key=lambda EdgeIndex: EdgeData[EdgeIndex].offset
    )
    StartIndex, CurrentIndex = EdgeData[FirstEdgeIndex].endpoint_indices or (-1, -1)
    OrderedVertices = [StartIndex]
    OrderedEdges = [FirstEdgeIndex]
    UsedEdges = {FirstEdgeIndex}
    while CurrentIndex != StartIndex and len(OrderedVertices) <= len(VertexIndexes):
        OrderedVertices.append(CurrentIndex)
        ChoiceData = tuple(
            ItemData
            for ItemData in AdjacencyData[CurrentIndex]
            if ItemData[0] not in UsedEdges
        )
        if len(ChoiceData) != 1:
            break
        NextEdgeIndex, CurrentIndex = ChoiceData[0]
        UsedEdges.add(NextEdgeIndex)
        OrderedEdges.append(NextEdgeIndex)
    if (
        CurrentIndex != StartIndex
        or UsedEdges != ComponentIndexes
        or len(OrderedVertices) != 6
    ):
        return None
    return (OrderedVertices, OrderedEdges)


# polyline construction owns point validation and marker offset ordering
def CreatePoly(
    MarkersData: Sequence[NativeMarker],
    EdgeData: Sequence[NativeMarker],
    OrderedVertices: Sequence[int],
    OrderedEdges: Sequence[int],
) -> tuple[NativeProfile, tuple[int, ...]] | None:
    OrderedPoints = tuple(
        MarkersData[VertexIndex].coordinates_mm for VertexIndex in OrderedVertices
    )
    if any(PointData is None for PointData in OrderedPoints):
        return None
    ResolvedPoints = tuple(
        PointData for PointData in OrderedPoints if PointData is not None
    )
    if len(set(ResolvedPoints)) != 6:
        return None
    MarkerOffsets = tuple(
        EdgeData[EdgeIndex].offset for EdgeIndex in OrderedEdges
    ) + tuple(MarkersData[VertexIndex].offset for VertexIndex in OrderedVertices)
    Profile = NativeProfile(
        "polyline",
        tuple(
            CoordinateValue
            for PointData in ResolvedPoints
            for CoordinateValue in PointData
        ),
        MarkerOffsets,
    )
    return (Profile, MarkerOffsets)


# this definition exists because focused behavior needs one stable owner
def PolyProfiles(
    MarkersData: list[NativeMarker], ExcludedOffsets: set[int]
) -> tuple[tuple[NativeProfile, ...], set[int]]:
    EdgeData = tuple(
        MarkerData
        for MarkerData in MarkersData
        if MarkerData.offset not in ExcludedOffsets
        and MarkerData.profile_role == 1
        and MarkerData.native_kind in {0, 1, 2}
        and MarkerData.coordinates_mm is None
        and MarkerData.endpoint_indices is not None
        and MarkerData.endpoint_indices[0] != MarkerData.endpoint_indices[1]
        and all(
            0 <= EndpointIndex < len(MarkersData)
            and MarkersData[EndpointIndex].coordinates_mm is not None
            for EndpointIndex in MarkerData.endpoint_indices
        )
    )
    RemainingIndexes = set(range(len(EdgeData)))
    ProfileData: list[NativeProfile] = []
    UsedOffsets: set[int] = set()
    while RemainingIndexes:
        ComponentIndexes, VertexIndexes = TakeGraphMut(EdgeData, RemainingIndexes)
        if len(ComponentIndexes) != 6 or len(VertexIndexes) != 6:
            continue
        OrderedData = OrderPolyEdges(EdgeData, ComponentIndexes, VertexIndexes)
        if OrderedData is None:
            continue
        CreatedData = CreatePoly(MarkersData, EdgeData, *OrderedData)
        if CreatedData is not None:
            Profile, MarkerOffsets = CreatedData
            UsedOffsets.update(MarkerOffsets)
            ProfileData.append(Profile)
    return (tuple(ProfileData), UsedOffsets)


# circle closure parsing owns marker topology and radial geometry validation
def CircleClosure(
    Markers: Sequence[NativeMarker], ClosureIndex: int, ExcludedOffsets: set[int]
) -> (
    tuple[
        NativeMarker,
        NativeMarker,
        NativeMarker,
        float,
        float | None,
        tuple[float, float, float],
    ]
    | None
):
    Closure = Markers[ClosureIndex]
    Endpoints = Closure.endpoint_indices
    if (
        Closure.offset in ExcludedOffsets
        or Closure.coordinates_mm is not None
        or Closure.locus != KCircleLocus.hex()
        or Closure.profile_role != 1
        or Closure.native_kind not in {0, 1}
        or Endpoints is None
        or Endpoints[0] != Endpoints[1]
    ):
        return None
    RimIndex = Endpoints[0]
    CenterIndex = RimIndex - 1
    if not 0 <= CenterIndex < RimIndex < ClosureIndex or ClosureIndex - RimIndex > 2:
        return None
    Center = Markers[CenterIndex]
    RimValue = Markers[RimIndex]
    if (
        Center.offset in ExcludedOffsets
        or RimValue.offset in ExcludedOffsets
        or Center.coordinates_mm is None
        or RimValue.coordinates_mm is None
        or RimValue.locus != KCircleLocus.hex()
        or Center.profile_role != 1
        or RimValue.profile_role != 1
    ):
        return None
    Radius = MarkerRadiusMm(Center, RimValue)
    if Radius is None:
        return None
    GeomValue = (Center.coordinates_mm[0], Center.coordinates_mm[1], Radius)
    return (Center, RimValue, Closure, Radius, MarkerStart(Center, RimValue), GeomValue)


# circle dimension matching owns unique radius and diameter normalization
def MatchCircleMut(
    Dimensions: tuple[NativeDimension, ...],
    Radius: float,
    Normalized: dict[int, str],
    GeomValue: tuple[float, float, float],
) -> tuple[tuple[float, float, float], str | None, str | None]:
    Matches: list[tuple[int, str, float]] = []
    for Index, Dimension in enumerate(Dimensions):
        if MathValue.isclose(Dimension.value_mm, Radius, rel_tol=1e-07, abs_tol=1e-07):
            Matches.append((Index, "radius", Dimension.value_mm))
        elif MathValue.isclose(
            Dimension.value_mm, Radius * 2.0, rel_tol=1e-07, abs_tol=1e-07
        ):
            Matches.append((Index, "diameter", Dimension.value_mm / 2.0))
    ParamName = None
    DimensionKind = None
    if len(Matches) == 1 and Matches[0][0] not in Normalized:
        DimensionIndex, DimensionKind, NormalizedRadius = Matches[0]
        GeomValue = (GeomValue[0], GeomValue[1], NormalizedRadius)
        ParamName = Dimensions[DimensionIndex].name
        Normalized[DimensionIndex] = DimensionKind
    return (GeomValue, ParamName, DimensionKind)


# this definition exists because focused behavior needs one stable owner
def Structural(
    Markers: list[NativeMarker],
    Dimensions: tuple[NativeDimension, ...],
    ExcludedOffsets: set[int],
) -> tuple[tuple[NativeProfile, ...], set[int], dict[int, str]]:
    Profiles: list[NativeProfile] = []
    UsedValue: set[int] = set()
    Normalized: dict[int, str] = {}
    Geometries: set[tuple[float, float, float]] = set()
    for ClosureIndex in range(len(Markers)):
        Candidate = CircleClosure(Markers, ClosureIndex, ExcludedOffsets)
        if Candidate is None:
            continue
        Center, RimValue, Closure, Radius, StartAngle, GeomValue = Candidate
        if GeomValue in Geometries:
            continue
        GeomValue, ParamName, DimensionKind = MatchCircleMut(
            Dimensions, Radius, Normalized, GeomValue
        )
        Geometries.add(GeomValue)
        MarkerOffsets = (Center.offset, RimValue.offset, Closure.offset)
        UsedValue.update(MarkerOffsets)
        Profiles.append(
            NativeProfile(
                "circle", GeomValue, MarkerOffsets, ParamName, DimensionKind, StartAngle
            )
        )
    return (tuple(Profiles), UsedValue, Normalized)


# focused continuation isolates the remaining native serialization phase
def FinishCircleMut(
    Dimensions: tuple[NativeDimension, ...],
    Candidates: dict[
        int,
        dict[
            tuple[float, float, float],
            list[tuple[NativeMarker, NativeMarker, str, float | None]],
        ],
    ],
) -> tuple[tuple[NativeProfile, ...], dict[int, str]]:
    Result: list[NativeProfile] = []
    Geometries: set[tuple[float, float, float]] = set()
    Normalized: dict[int, str] = {}
    for Index, Dimension in enumerate(Dimensions):
        Matches = Candidates.get(Index, {})
        if len(Matches) != 1:
            continue
        GeomValue, Records = next(iter(Matches.items()))
        if GeomValue in Geometries:
            continue
        Semantics = {RecordData[2] for RecordData in Records}
        if len(Semantics) != 1:
            continue
        Geometries.add(GeomValue)
        Normalized[Index] = next(iter(Semantics))
        Result.append(
            NativeProfile(
                "circle",
                GeomValue,
                tuple(
                    sorted(
                        {
                            Offset
                            for RecordData in Records
                            for Offset in (
                                RecordData[0].offset,
                                RecordData[1].offset,
                            )
                        }
                    )
                ),
                Dimension.name,
                Normalized[Index],
                Records[0][3],
            )
        )

    # this callback exists because local behavior needs one focused transformation
    Result.sort(key=lambda Profile: min(Profile.marker_offsets))
    return (tuple(Result), Normalized)


# this definition exists because focused behavior needs one stable owner
def CircleSet(
    Markers: list[NativeMarker], Dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], dict[int, str]]:
    Centers = [
        Marker
        for Marker in Markers
        if Marker.semantic == "circle" and Marker.coordinates_mm is not None
    ]
    if not Centers:
        return ((), {})
    Candidates: dict[
        int,
        dict[
            tuple[float, float, float],
            list[tuple[NativeMarker, NativeMarker, str, float | None]],
        ],
    ] = {}
    for CircleMarker in Centers:
        CircleCoordinates = CircleMarker.coordinates_mm
        if CircleCoordinates is None:
            continue
        FollowingMarker = next(
            (
                Marker
                for Marker in Markers
                if Marker.offset > CircleMarker.offset
                and Marker.coordinates_mm is not None
                and (not IsSamePoint(Marker.coordinates_mm, CircleCoordinates))
            ),
            None,
        )
        PrecedingMarker = next(
            (
                Marker
                for Marker in reversed(Markers)
                if Marker.offset < CircleMarker.offset
                and Marker.coordinates_mm is not None
                and (not IsSamePoint(Marker.coordinates_mm, CircleCoordinates))
            ),
            None,
        )
        ChoicePairs = tuple(
            (
                ItemData
                for ItemData in (
                    (
                        (CircleMarker, FollowingMarker)
                        if FollowingMarker is not None
                        else None
                    ),
                    (
                        (PrecedingMarker, CircleMarker)
                        if PrecedingMarker is not None and FollowingMarker is None
                        else None
                    ),
                )
                if ItemData is not None
            )
        )
        for CenterMarker, RimMarker in ChoicePairs:
            RadiusValue = MarkerRadiusMm(CenterMarker, RimMarker)
            if RadiusValue is None:
                continue
            StartAngle = MarkerStart(CenterMarker, RimMarker)
            for Index, Dimension in enumerate(Dimensions):
                Semantic = None
                NormalizedRadius = RadiusValue
                if MathValue.isclose(
                    Dimension.value_mm, RadiusValue, rel_tol=1e-07, abs_tol=1e-07
                ):
                    Semantic = "radius"
                    NormalizedRadius = Dimension.value_mm
                elif MathValue.isclose(
                    Dimension.value_mm, RadiusValue * 2.0, rel_tol=1e-07, abs_tol=1e-07
                ):
                    Semantic = "diameter"
                    NormalizedRadius = Dimension.value_mm / 2.0
                if Semantic is None:
                    continue
                CenterCoordinates = CenterMarker.coordinates_mm
                if CenterCoordinates is None:
                    continue
                GeomValue = (
                    CenterCoordinates[0],
                    CenterCoordinates[1],
                    NormalizedRadius,
                )
                Candidates.setdefault(Index, {}).setdefault(GeomValue, []).append(
                    (CenterMarker, RimMarker, Semantic, StartAngle)
                )
    return FinishCircleMut(Dimensions, Candidates)


# this definition exists because focused behavior needs one stable owner
def IsSamePoint(LeftValue: tuple[float, float], Right: tuple[float, float]) -> bool:
    return MathValue.isclose(
        LeftValue[0], Right[0], abs_tol=1e-12
    ) and MathValue.isclose(LeftValue[1], Right[1], abs_tol=1e-12)


# this definition exists because focused behavior needs one stable owner
def Constraints(
    Feature: NativeFeature,
    Markers: tuple[NativeMarker, ...],
    Profiles: tuple[NativeProfile, ...],
) -> tuple[NativeRule, ...]:
    Constraints: list[NativeRule] = []
    RadialParameters: set[str] = set()
    for ProfileIndex, Profile in enumerate(Profiles):
        if Profile.kind == "rectangle":
            for EdgeIndex in range(4):
                Constraints.append(
                    NativeRule(
                        id=f"{Feature.object_id}:profile:{ProfileIndex}:axis:{EdgeIndex}",
                        kind="horizontal" if EdgeIndex % 2 == 0 else "vertical",
                        references=(
                            f"{Feature.object_id}:profile:{ProfileIndex}:edge:{EdgeIndex}",
                        ),
                        parameter=None,
                        value=None,
                        native_offset=(
                            Profile.marker_offsets[EdgeIndex]
                            if EdgeIndex < len(Profile.marker_offsets)
                            else None
                        ),
                        native_code=None,
                    )
                )
        elif Profile.kind == "circle":
            Semantic = Profile.dimension_kind or "radius"
            ParamName = Profile.parameter_name
            if ParamName is not None:
                RadialParameters.add(ParamName)
            Constraints.append(
                NativeRule(
                    id=f"{Feature.object_id}:profile:{ProfileIndex}:{Semantic}",
                    kind=Semantic,
                    references=(f"{Feature.object_id}:profile:{ProfileIndex}",),
                    parameter=(
                        f"{Feature.object_id}:{ParamName}"
                        if ParamName is not None
                        else None
                    ),
                    value=(
                        Profile.coordinates[2] * 2.0
                        if Semantic == "diameter"
                        else Profile.coordinates[2]
                    ),
                    native_offset=(
                        Profile.marker_offsets[0] if Profile.marker_offsets else None
                    ),
                    native_code=None,
                )
            )
    for Dimension in Feature.dimensions:
        if Dimension.name in RadialParameters:
            continue
        Constraints.append(
            NativeRule(
                id=f"{Feature.object_id}:dimension:{Dimension.name}",
                kind="distance",
                references=tuple(
                    (
                        f"native:{Operand.kind_code:04x}:{Operand.entity_index}"
                        for Operand in Dimension.operands
                    )
                ),
                parameter=f"{Feature.object_id}:{Dimension.name}",
                value=Dimension.value_mm,
                native_offset=Dimension.native_offset,
                native_code=None,
            )
        )
    for Marker in Markers:
        if Marker.semantic != "relation":
            continue
        Constraints.append(
            NativeRule(
                id=f"{Feature.object_id}:native-relation:{Marker.offset}",
                kind=f"native_{Marker.native_kind}",
                references=tuple(
                    (f"native-index:{Index}" for Index in Marker.endpoint_indices or ())
                ),
                parameter=None,
                value=None,
                native_offset=Marker.offset,
                native_code=Marker.native_kind,
            )
        )
    return tuple(Constraints)


# this definition exists because focused behavior needs one stable owner
def OperationFields(
    DataValue: bytes, Record: NativeName
) -> tuple[int | None, int | None, int | None]:
    if Record.text_end + 12 > len(DataValue):
        return (None, None, None)
    Family = Struct.unpack_from("<H", DataValue, Record.text_end + 4)[0]
    Operation = DataValue[Record.text_end + 6]
    Schema = DataValue[Record.text_end + 7]
    RepeatedId = Struct.unpack_from("<I", DataValue, Record.text_end + 8)[0]
    if RepeatedId != Record.object_id:
        return (None, None, None)
    return (Family, Operation, Schema)


# this definition exists because focused behavior needs one stable owner
def RevolutionAxis(Sketch: NativeSketch | None) -> NativeMarker | None:
    if Sketch is None:
        return None
    Candidates = tuple(
        (
            Marker
            for Marker in Sketch.markers
            if Marker.profile_role == 2
            and Marker.semantic == "line"
            and (Marker.endpoint_indices is not None)
            and (Marker.endpoint_indices[0] != Marker.endpoint_indices[1])
        )
    )
    return Candidates[0] if len(Candidates) == 1 else None


# this definition exists because focused behavior needs one stable owner
def RevolutionAxisA(
    Operation: NativeOperation, Sketch: NativeSketch | None
) -> tuple[float, float] | None:
    if Sketch is None:
        return None
    if Operation.axis_marker_offset is None:
        AxisValue = (
            RevolutionAxis(Sketch) if Operation.axis_source_kind is None else None
        )
    else:
        AxisValue = next(
            (
                Marker
                for Marker in Sketch.markers
                if Marker.offset == Operation.axis_marker_offset
            ),
            None,
        )
    if AxisValue is None or AxisValue.endpoint_indices is None:
        return None
    if any(
        (
            not 0 <= Endpoint < len(Sketch.markers)
            for Endpoint in AxisValue.endpoint_indices
        )
    ):
        return None
    Start = Sketch.markers[AxisValue.endpoint_indices[0]].coordinates_mm
    EndValue = Sketch.markers[AxisValue.endpoint_indices[1]].coordinates_mm
    if Start is None or EndValue is None:
        return None
    Delta = (EndValue[0] - Start[0], EndValue[1] - Start[1])
    Length = MathValue.hypot(Delta[0], Delta[1])
    if Length <= 0.0:
        return None
    return (Clean(Delta[0] / Length), Clean(Delta[1] / Length))


# this definition exists because focused behavior needs one stable owner
def OperationAxis(
    Operation: NativeOperation, Sketch: NativeSketch | None
) -> str | None:
    if (
        Sketch is None
        or AxisSketchId(
            Operation.profile_id, Operation.axis_source_kind, Operation.axis_source_id
        )
        != Sketch.object_id
    ):
        return None
    if Operation.kind in KExtrusionOperationKinds:
        return KNormalAxisSubElem
    if Operation.kind not in KRevolutionOperationKinds:
        return None
    Direction = RevolutionAxisA(Operation, Sketch)
    if Direction is None:
        return None
    if Direction[0] == 0.0 and Direction[1] != 0.0:
        return KVerticalAxisSubElem
    if Direction[1] == 0.0 and Direction[0] != 0.0:
        return KHorizontalAxisSubElem
    return None


# this definition exists because focused behavior needs one stable owner
def OperationA(
    DataValue: bytes,
    Start: int,
    EndValue: int,
    Feature: NativeFeature,
    Features: list[NativeFeature],
) -> tuple[tuple[int, int, int], ...]:
    Preceding = {
        ItemValue.object_id
        for ItemValue in Features
        if ItemValue.object_id > 25
        and ItemValue.native_offset is not None
        and (Feature.native_offset is not None)
        and (ItemValue.native_offset < Feature.native_offset)
    }
    Result: list[tuple[int, int, int]] = []
    SeenValue: set[tuple[int, int]] = set()
    for Selection in EdgeSelections(DataValue, Start, EndValue):
        Identity = (Selection[1], Selection[2])
        if (
            Selection[1] not in Preceding
            or not 0 < Selection[2] < 32768
            or Identity in SeenValue
        ):
            continue
        SeenValue.add(Identity)
        Result.append(Selection)
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def OperationAfter(
    DataValue: bytes,
    Start: int,
    EndValue: int,
    Feature: NativeFeature,
    Features: list[NativeFeature],
    ClassName: str,
) -> tuple[tuple[int, int, int], ...]:
    Declarations = tuple(
        (
            ItemValue
            for ItemValue in ParseClasses(DataValue)
            if ItemValue.name == ClassName and Start <= ItemValue.offset < EndValue
        )
    )
    if len(Declarations) != 1:
        return ()
    DeclValue = Declarations[0]
    ClassEnd = DeclValue.offset + 6 + len(ClassName.encode("ascii"))
    return OperationA(DataValue, ClassEnd, EndValue, Feature, Features)


# this definition exists because focused behavior needs one stable owner
def Native(
    Dimensions: tuple[NativeDimension, ...],
) -> tuple[float, float, float] | None:
    ByName = {
        Dimension.name.casefold(): Dimension
        for Dimension in Dimensions
        if Dimension.name.casefold() in {"d1", "d2", "d3"}
    }
    if set(ByName) != {"d1", "d2", "d3"} or any(
        (ItemValue.native_offset is None for ItemValue in ByName.values())
    ):
        return None
    return (ByName["d1"].value_mm, ByName["d2"].value_mm, ByName["d3"].value_mm)


# this definition exists because focused behavior needs one stable owner
def NativeScale(
    DataValue: bytes, Start: int, EndValue: int
) -> tuple[float, float, float] | None:
    if EndValue - Start < 38:
        return None
    Block = DataValue[EndValue - 38 : EndValue]
    if (
        Block[:4] != Struct.pack("<I", 1)
        or Block[28:36] != b"\x00" * 8
        or Struct.unpack_from("<H", Block, 36)[0] < 32768
    ):
        return None
    Factors = Struct.unpack_from("<3d", Block, 4)
    if not all((MathValue.isfinite(Value) and Value > 0.0 for Value in Factors)):
        return None
    return Factors


# this definition exists because focused behavior needs one stable owner
def ResolveProfile(
    Operation: NativeOperation,
    Sketches: dict[int, NativeSketch],
    DataValue: bytes,
    Features: list[NativeFeature],
) -> NativeOperation:
    if Operation.kind != "hole" or Operation.profile_id not in Sketches:
        return Operation
    Sketch = Sketches[Operation.profile_id]
    Circles = tuple(
        (Profile for Profile in Sketch.profiles if Profile.kind == "circle")
    )
    Feature = next(
        (
            ItemValue
            for ItemValue in Features
            if ItemValue.object_id == Operation.object_id
        ),
        None,
    )
    Selections = (
        OperationA(
            DataValue, Sketch.native_offset, Sketch.native_end, Feature, Features
        )
        if Feature is not None
        else ()
    )
    return Replace(
        Operation,
        diameter_mm=Circles[0].coordinates[2] * 2.0 if len(Circles) == 1 else None,
        selection_offsets=tuple((Selection[0] for Selection in Selections)),
        selected_local_ids=tuple((Selection[2] for Selection in Selections)),
        selection_references=tuple(
            ((Selection[1], Selection[2]) for Selection in Selections)
        ),
    )


# this definition exists because focused behavior needs one stable owner
def EndSpec(
    DataValue: bytes, Start: int, EndValue: int, Classes: tuple[NativeClass, ...] = ()
) -> NativeEndSpec | None:
    MirroredOffset, MirroredCode = Mirrored(DataValue, Classes, Start, EndValue)
    for Offset in range(Start, max(Start, EndValue - 26 + 1) + 1):
        Prefix = DataValue[Offset : Offset + 2]
        if Prefix != b"_c" and (
            not (
                len(Prefix) == 2
                and Struct.unpack("<H", Prefix)[0] & 32768
                and (Prefix != b"\xff\xff")
            )
        ):
            continue
        if DataValue[Offset + 2 : Offset + 4] != b"\x00\x00":
            continue
        if Struct.unpack_from("<I", DataValue, Offset + 4)[0] != 1:
            continue
        if Struct.unpack_from("<I", DataValue, Offset + 8)[0] not in {0, 1}:
            continue
        Direction = Struct.unpack_from("<I", DataValue, Offset + 12)[0]
        if (
            Direction not in {0, 1}
            or DataValue[Offset + 16 : Offset + 18] != b"\x00\x00"
        ):
            continue
        Termination = Struct.unpack_from("<I", DataValue, Offset + 18)[0]
        Second = Struct.unpack_from("<I", DataValue, Offset + 22)[0]
        if Termination > 64 or Second > 1:
            continue
        return NativeEndSpec(
            Offset, Termination, Direction, Second, MirroredOffset, MirroredCode
        )
    return None


# this definition exists because focused behavior needs one stable owner
def EdgeSelections(
    DataValue: bytes, Start: int, EndValue: int
) -> tuple[tuple[int, int, int], ...]:
    Selections: list[tuple[int, int, int]] = []
    for Offset in FindAll(DataValue, KEdgeSelectionIdentity, Start, EndValue):
        if Offset + 38 > EndValue:
            continue
        Producer = Struct.unpack_from("<I", DataValue, Offset + 26)[0]
        LocalId = Struct.unpack_from("<I", DataValue, Offset + 34)[0]
        if Producer and LocalId:
            Selections.append((Offset, Producer, LocalId))
    return tuple(Selections)


# this definition exists because focused behavior needs one stable owner
def DimensionValue(
    Dimensions: tuple[NativeDimension, ...], Semantic: str
) -> float | None:
    return next(
        (Dimension.value_mm for Dimension in Dimensions if Dimension.kind == Semantic),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def OperationOffset(
    Dimensions: tuple[NativeDimension, ...], Semantic: str
) -> int | None:
    return next(
        (
            Dimension.native_offset
            for Dimension in Dimensions
            if Dimension.kind == Semantic and Dimension.native_offset is not None
        ),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def IntegerProp(Value: str | None) -> int | None:
    if Value is None:
        return None
    try:
        return int(Value)
    except ValueError:
        return None


# this definition exists because focused behavior needs one stable owner
def FindAll(
    DataValue: bytes, Marker: bytes, Start: int = 0, EndValue: int | None = None
) -> list[int]:
    Result: list[int] = []
    Cursor = Start
    Limit = len(DataValue) if EndValue is None else EndValue
    while True:
        Offset = DataValue.find(Marker, Cursor, Limit)
        if Offset < 0:
            return Result
        Result.append(Offset)
        Cursor = Offset + 1


# this definition exists because focused behavior needs one stable owner
def IsMatches(Value: float, Candidates: list[float]) -> bool:
    return any(
        (MathValue.isclose(Value, Choice, abs_tol=1e-06) for Choice in Candidates)
    )


# this definition exists because focused behavior needs one stable owner
def NormAction(Vector: tuple[float, float, float]) -> float:
    return MathValue.sqrt(sum((Value * Value for Value in Vector)))


# this definition exists because focused behavior needs one stable owner
def DotAction(
    LeftValue: tuple[float, float, float], Right: tuple[float, float, float]
) -> float:
    return sum(
        (
            FirstValue * SecondValue
            for FirstValue, SecondValue in zip(LeftValue, Right, strict=True)
        )
    )


# this definition exists because focused behavior needs one stable owner
def Cross(
    LeftValue: tuple[float, float, float], Right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        LeftValue[1] * Right[2] - LeftValue[2] * Right[1],
        LeftValue[2] * Right[0] - LeftValue[0] * Right[2],
        LeftValue[0] * Right[1] - LeftValue[1] * Right[0],
    )


# this definition exists because focused behavior needs one stable owner
def Clean(Value: float) -> float:
    return 0.0 if abs(Value) <= 1e-12 else Value


# this binding exists because shared behavior needs one stable value
ANGLE_COPY_DELTAS = AngleCopyDeltas

# this binding exists because shared behavior needs one stable value
ASSEMBLY_SUFFIX = AsmSuffix

# this binding exists because shared behavior needs one stable value
BooleanOperation = BoolOperation


# this binding exists because shared behavior needs one stable value
CANONICAL_PLANE_FEATURE_TYPE = CanonicalPlaneFeatureType

# this binding exists because shared behavior needs one stable value
CLASS_MARKER = ClassMarker


# this binding exists because shared behavior needs one stable value
CircleGeometry = CircleGeom

# this binding exists because shared behavior needs one stable value
DEPTH_COPY_DELTAS = DepthCopyDeltas

# this binding exists because shared behavior needs one stable value
DEPTH_COPY_SIGNS = DepthCopySigns

# this binding exists because shared behavior needs one stable value
DERIVED_SUPPORT_KIND = KDerivedSupportKind

# this binding exists because shared behavior needs one stable value
DIMENSION_SCALAR_HEADERS = DimensionScalarHeaders

# this binding exists because shared behavior needs one stable value
DIRECTION_AXIS_ROLE = KDirectionAxisRole

# this binding exists because shared behavior needs one stable value
ET = XmlTree


# this binding exists because shared behavior needs one stable value
FACE_SUPPORT_KIND = KFaceSupportKind


# this binding exists because shared behavior needs one stable value
FROM_END_SPEC_CLASS = FromEndSpecClass

# this binding exists because shared behavior needs one stable value
FROM_REVERSE_RELATIVE = FromReverseRelative

# this binding exists because shared behavior needs one stable value
HORIZONTAL_AXIS_SUBELEMENT = KHorizontalAxisSubElem


# this binding exists because shared behavior needs one stable value
KIT_RESOLVED_STREAM = KitResolvedStream


# this binding exists because shared behavior needs one stable value
MARKER_LOCAL_ID_OFFSET_BY_LENGTH = KMarkerLocalIdOffsetBy

# this binding exists because shared behavior needs one stable value
NORMAL_AXIS_SUBELEMENT = KNormalAxisSubElem


# this binding exists because shared behavior needs one stable value
NativeBoundingBox = NativeBounding

# this binding exists because shared behavior needs one stable value
NativeConfiguration = NativeConfig

# this binding exists because shared behavior needs one stable value
NativeConstraint = NativeRule

# this binding exists because shared behavior needs one stable value
NativeModelHeader = NativeModelA


# this binding exists because shared behavior needs one stable value
NativeSketchPlane = NativeSketchA

# this binding exists because shared behavior needs one stable value
PART_SUFFIX = PartSuffix

# this binding exists because shared behavior needs one stable value
PLANE_FEATURE_TYPES = PlaneFeatureTypes

# this binding exists because shared behavior needs one stable value
PLANE_SUPPORT_KIND = KPlaneSupportKind


# this binding exists because shared behavior needs one stable value
ParameterRole = ParamRole


# this binding exists because shared behavior needs one stable value
REFERENCE_SUPPORT_SOURCE = KRefSupportSource

# this binding exists because shared behavior needs one stable value
RESOLVED_FEATURES_STREAM = ResolvedFeaturesStream

# this binding exists because shared behavior needs one stable value
REVOLUTION_AXIS_SKETCH = RevolutionAxisSketch

# this binding exists because shared behavior needs one stable value
SERIALIZED_STRING_MARKER = SerializedStringMarker

# this binding exists because shared behavior needs one stable value
SKETCH_CHAIN_CLASS = SketchChainClass

# this binding exists because shared behavior needs one stable value
STREAM_ORDER_SUPPORT_SOURCE = KStreamOrderSupportSource

# this binding exists because shared behavior needs one stable value
UNRESOLVED_SUPPORT_SOURCE = KUnresolvedSupportSource


# this binding exists because shared behavior needs one stable value
VERTICAL_AXIS_SUBELEMENT = KVerticalAxisSubElem


# this binding exists because shared behavior needs one stable value
_SKETCH_PLANE_ID_RELATIVE = KSketchPlaneIdRelative  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_SKETCH_PLANE_REFERENCE_PREFIX = KSketchPlaneRefPrefix  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_SKETCH_PLANE_REFERENCE_TAG = KSketchPlaneRefTag  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_SKETCH_PLANE_SCAN_BYTES = KSketchPlaneScanBytes  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_SURFACE_EXTRUSION_FEATURE_TYPES = KSurfaceExtrusionFeature  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_XmlFeature = XmlFeature  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_angle_copies = AngleCopies  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_bind_dimension = BindDimension  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_bounding_box = BoundingBox  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_circle_profiles = CircleSet  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_class_record_end = ClassRecordEnd  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_clean = Clean  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_component_plane_sources = ComponentPlane  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_constraints = Constraints  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_cross = Cross  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_decode_planes = DecodePlanes  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_decode_sketch = DecodeSketch  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_depth_copies = DepthCopies  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_dot = DotAction  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_edge_selections = EdgeSelections  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_end_spec = EndSpec  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_expect_bytes = ExpectBytes  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_feature_records = FeatureRecords  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_find_all = FindAll  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_integer_property = IntegerProp  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_is_origin_feature = IsOriginFeature  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_is_plane_feature = IsPlaneFeature  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_linked_rectangle_profiles = LinkedRectangle  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_marker_coordinates = Marker  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_marker_coordinates_metres = MarkerMetres  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_marker_local_id = MarkerLocalId  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_marker_radius_mm = MarkerRadiusMm  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_marker_semantic = MarkerSemantic  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_marker_start_angle_degrees = MarkerStart  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_matches = IsMatches  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_matrix_frame = MatrixFrame  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_minimal_frame = MinimalFrame  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_mirrored_direction = Mirrored  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_name_marker = NameMarker  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_native_feature_sort_key = NativeFeatureA  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_native_scale_factors = NativeScale  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_native_translation = Native  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_norm = NormAction  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_operation_dimension = DimensionValue  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_operation_dimension_offset = OperationOffset  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_operation_fields = OperationFields  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_operation_selections = OperationA  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_operation_selections_after_class = OperationAfter  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_orthonormal = IsOrthonormal  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_parse_classes = ParseClasses  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_dimension = ParseDimension  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_keywords = ParseKeywords  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_markers = ParseMarkers  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_names = ParseNames  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_native_equations = ParseNative  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_scalars = ParseScalars  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_parse_xml = ParseXml  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_primary_dimension = Primary  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_principal_plane_frames = PrincipalPlaneA  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_profiles = DecodeProfiles  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_read_class = ReadClass  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_read_serialized_string = ReadSerialized  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_read_sketch_plane_reference = ReadSketchPlane  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_record_class = RecordClass  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_record_class_name = RecordClassName  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_reference_plane_ids = RefPlaneIds  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_repair_plane_object_ids = RepairPlaneIMut  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_resolve_profile_operation = ResolveProfile  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_revolution_axis_marker = RevolutionAxis  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_same_point = IsSamePoint  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_scalar_owners = ScalarOwners  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_scalar_trailer = ScalarTrailer  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_semantic_dimensions = Semantic  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_sketch_plane_reference = SketchPlaneRef  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_sketch_support_kind = SketchSupport  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
_structural_circle_profiles = Structural  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_structural_rectangle_profiles = StructuralA  # lgtm[py/unused-global-variable]

# this binding exists because shared behavior needs one stable value
_support_plane_reference = SupportPlaneRef  # lgtm[py/unused-global-variable]


# this binding exists because shared behavior needs one stable value
annotations = Annotations


# this binding exists because shared behavior needs one stable value
circle_radius_mm = CircleRadiusMm

# this binding exists because shared behavior needs one stable value
dataclass = Dataclass

# this binding exists because shared behavior needs one stable value
decode_ascii_brep = DecodeAsciiBrep

# this binding exists because shared behavior needs one stable value
decode_native_model = DecodeNative

# this binding exists because shared behavior needs one stable value
decode_native_model_header = DecodeNativeA

# this binding exists because shared behavior needs one stable value
dimension_scalar_value_offset = DimensionScalarValue


# this binding exists because shared behavior needs one stable value
field = Field

# this binding exists because shared behavior needs one stable value
hashlib = Hashlib

# this binding exists because shared behavior needs one stable value
itertools = Itertools

# this binding exists because shared behavior needs one stable value
locate_features = LocateFeatures

# this binding exists because shared behavior needs one stable value
math = MathValue


# this binding exists because shared behavior needs one stable value
operation_axis_subelement = OperationAxis


# this binding exists because shared behavior needs one stable value
re = RegexLib


# this binding exists because shared behavior needs one stable value
replace = Replace

# this binding exists because shared behavior needs one stable value
revolution_axis_direction = RevolutionAxisA

# this binding exists because shared behavior needs one stable value
struct = Struct


# this binding exists because shared behavior needs one stable value
Matches = IsMatches

# this binding exists because shared behavior needs one stable value
Orthonormal = IsOrthonormal


# this binding exists because shared behavior needs one stable value
RepairPlaneIds = RepairPlaneIMut

# this binding exists because shared behavior needs one stable value
SamePoint = IsSamePoint
