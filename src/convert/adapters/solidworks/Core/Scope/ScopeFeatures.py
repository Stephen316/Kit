from dataclasses import replace as Replace
from math import isclose as IsClose
from typing import Mapping as TypeMap

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Resolved.BossDepth import DepthParam
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopedCut, ScopeOwner
from convert.adapters.solidworks.Resolved.Scope.Boss import ScopeBoss
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue


# scoped operations reuse the public feature identity only after its original native name matches
def CheckScopeFeat(StepValue: FeatureStep, NativeId: int, NameValue: str) -> None:
    RequireArch(
        (StepValue.id, StepValue.name, StepValue.kind, StepValue.suppressed),
        (f"sldprt:feature:{NativeId}", NameValue, FeatureKind.EXTRUSION, False),
        "active scoped extrusion owner",
    )


# a signed operation role retains the positive editable dimension in its native provenance
def ScopeDim(
    Saved: DepthParam,
    StepValue: FeatureStep,
    Parameters: TypeMap[str, Parameter],
    StreamName: str,
    RoleValue: str,
    SignedMetres: float,
) -> Parameter:
    Identity = f"sldprt:parameter:{StepValue.attributes['native_object_id']}:{Saved['parameter_name']}"
    ParameterValueSource = Parameters[Identity]
    Quantity = ParameterValueSource.value
    RequireArch(
        ParameterValueSource.owner_id == StepValue.id
        and Identity in StepValue.parameter_ids
        and ParameterValueSource.name == Saved["parameter_name"]
        and Quantity.kind == ValueKind.LENGTH
        and Quantity.unit == "mm"
        and type(Quantity.value) in (int, float)
        and IsClose(
            float(Quantity.value), Saved["metres"] * 1000, rel_tol=0, abs_tol=1e-8
        ),
        True,
        "scoped feature dimension matches its typed parameter",
    )
    return Replace(
        ParameterValueSource,
        provenance=RectSource(
            str(Saved["parameter_object"]),
            StreamName,
            MemberSpan(Saved["offset"], Saved["end"]),
            "scoped-extrusion-parameter",
        ),
        attributes=FreezeMapping(
            {
                **ParameterValueSource.attributes,
                "native_dimension_id": Saved["native_dimension_id"],
                "extrusion_parameter_role": RoleValue,
                "extrusion_direction_sign": -1 if SignedMetres < 0 else 1,
            }
        ),
    )


# separately owned boss atoms create independent solids with their own sketch and extent
def ScopeBossStep(
    StepValue: FeatureStep,
    BossValue: ScopeBoss,
    Parameters: TypeMap[str, Parameter],
    StreamName: str,
) -> tuple[FeatureStep, tuple[Parameter, ...]]:
    CheckScopeFeat(StepValue, BossValue.Owner.FeatureId, BossValue.Node["name"])
    SketchValue = BossValue.Profile.Sketch
    Extent = BossValue.Extent
    Depth = ScopeDim(
        Extent.Depth["dimension"],
        StepValue,
        Parameters,
        StreamName,
        "depth",
        Extent.DepthMetres,
    )
    Dimensions = (
        (Depth,)
        if Extent.Start is None
        else (
            Depth,
            ScopeDim(
                Extent.Start["dimension"],
                StepValue,
                Parameters,
                StreamName,
                "start_offset",
                Extent.StartMetres,
            ),
        )
    )
    RequireArch(
        set(StepValue.parameter_ids),
        {ParameterRow.id for ParameterRow in Dimensions},
        "scoped boss parameter roster",
    )
    Definition = ExtrudeFeature(
        length=Depth.value,
        end_condition=ExtrudeEnd.BLIND,
        reversed=Extent.DepthMetres < 0,
        direction=SpaceVector(*BossValue.Profile.Directions[2]),
        offset=(
            None
            if Extent.Start is None
            else ParameterValue(Extent.StartMetres * 1000, ValueKind.LENGTH, "mm")
        ),
    )
    return (
        Replace(
            StepValue,
            input_feature_ids=(f"sldprt:feature:{SketchValue.FeatureId}",),
            sketch_id=f"sldprt:sketch:{SketchValue.FeatureId}",
            operation=BooleanOp.CREATE,
            definition=Definition,
            provenance=RectSource(
                str(BossValue.Owner.FeatureId),
                StreamName,
                MemberSpan(BossValue.Node["offset"], Extent.End),
                "scoped-boss",
            ),
        ),
        Dimensions,
    )


# an explicit scope pick addresses the stable body and carries its typed earlier owner
def ScopeBodyPicks(CutValue: ScopedCut, StreamName: str) -> tuple[Selection, ...]:
    FeatureId = CutValue["native_feature_id"]
    return tuple(
        Selection(
            id=f"sldprt:selection:{FeatureId}:body:{BodyValue['body_id']}",
            name=f"Cut body {BodyValue['body_id']}",
            path=(SelectPathElem("body", f"sldprt:body:{BodyValue['body_id']}"),),
            query=FreezeMapping(
                {
                    "role": "extrusion_scope",
                    "native_producer_feature_id": BodyValue["feature_id"],
                }
            ),
            provenance=RectSource(
                str(BodyValue["object_index"]),
                StreamName,
                MemberSpan(BodyValue["offset"], BodyValue["end"]),
                "cut-scope-body",
            ),
        )
        for BodyValue in CutValue["primary_bodies"]["bodies"]
    )


# the authored selection is distinct from the measured effect of the saved operation
def ScopeCutStep(
    StepValue: FeatureStep,
    CutValue: ScopedCut,
    SketchId: int,
    Owners: tuple[ScopeOwner, ScopeOwner],
    Selected: tuple[Selection, ...],
    Affected: tuple[str, ...],
    Normal: SpaceVector,
    StreamName: str,
) -> FeatureStep:
    CutId = CutValue["native_feature_id"]
    CheckScopeFeat(StepValue, CutId, CutValue["name"])
    RequireArch(StepValue.parameter_ids, (), "depthless scoped cut parameters")
    Definition = ScopedExtrude(
        ExtrudeFeature(None, ExtrudeEnd.THROUGH_ALL, reversed=True, direction=Normal),
        "all_applicable" if CutValue["scope_kind"] == "all_bodies" else "explicit",
        tuple(f"sldprt:body:{NativeId}" for NativeId in CutValue["scope_body_ids"]),
        Affected,
    )
    return Replace(
        StepValue,
        input_feature_ids=tuple(
            f"sldprt:feature:{Owner.FeatureId}"
            for Owner in Owners
            if Owner.TransferObject in CutValue["parent_transfers"]
        )
        + (f"sldprt:feature:{SketchId}",),
        sketch_id=f"sldprt:sketch:{SketchId}",
        operation=BooleanOp.CUT,
        definition=Definition,
        selection_ids=tuple(PickValue.id for PickValue in Selected),
        provenance=RectSource(
            str(CutId),
            StreamName,
            MemberSpan(CutValue["offset"], CutValue["stream_end"]),
            "scoped-cut",
        ),
    )
