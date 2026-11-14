from dataclasses import replace as Replace

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.records.RecordProvenance import Provenance, ProvenanceSpan


# the originating record allows independent checks of every projected numeric value
def ParamOrigin(SpanValue: RecordSpan) -> Provenance:
    return Provenance(
        adapter="fusion.f3d",
        native_id=str(SpanValue.ObjectId),
        spans=(
            ProvenanceSpan(
                stream=KDesignPrefix + "BulkStream.dat",
                offset=SpanValue.StartOffset,
                length=SpanValue.EndOffset - SpanValue.StartOffset,
                record_kind=SpanValue.ClassGuid,
            ),
        ),
    )


# stored angles and lengths retain their native base units independently of display
def ParamQuantity(ParamData: NativeParam) -> ParameterValue:
    if ParamData.DisplayUnit in ("deg", "rad"):
        return ParameterValue(value=ParamData.Number, kind=ValueKind.KAngle, unit="rad")
    if ParamData.DisplayUnit in ("mm", "cm", "m", "in", "ft"):
        return ParameterValue(value=ParamData.Number, kind=ValueKind.KLength, unit="cm")
    if ParamData.DisplayUnit in ("", "unitless"):
        return ParameterValue(value=ParamData.Number)
    raise ValueError("Unsupported Fusion numeric parameter unit")


# retain vendor field identities while keeping feature ownership pending native binding validation
def ProjectParam(ParamData: NativeParam, SpanValue: RecordSpan) -> Parameter:
    return Parameter(
        id=f"fusion-parameter-{SpanValue.ObjectId}",
        name=ParamData.ParamName,
        value=ParamQuantity(ParamData),
        role=(
            ParameterRole.KDriving
            if ParamData.BindingId is None
            else ParameterRole.KReference
        ),
        expression=(
            Expression(source=ParamData.Formula, language="fusion")
            if ParamData.Formula
            else None
        ),
        provenance=ParamOrigin(SpanValue),
        attributes=FreezeMapping(
            {
                "fusion.display_unit": ParamData.DisplayUnit,
                "fusion.native_role": ParamData.RoleName,
                "fusion.binding_id": ParamData.BindingId,
                "fusion.parameter_index": ParamData.NativeIndex,
                "fusion.collection_id": ParamData.CollectionId,
                "fusion.expression_metadata": ParamData.Metadata.hex(),
                "fusion.comment": ParamData.Comment,
            }
        ),
    )


# only proven native relationships enter the neutral parameter attributes
def AttachOwner(
    ParamValue: Parameter, OwnerSpan: RecordSpan, Binding: RecordSpan
) -> Parameter:
    Origin = ParamValue.provenance
    if Origin is None:
        raise ValueError("Fusion parameter source span is missing")
    return Replace(
        ParamValue,
        provenance=Replace(Origin, spans=Origin.spans + ParamOrigin(Binding).spans),
        attributes=FreezeMapping(
            {
                **ParamValue.attributes,
                "fusion.owner_object_id": OwnerSpan.ObjectId,
                "fusion.owner_class_guid": OwnerSpan.ClassGuid,
            }
        ),
    )
