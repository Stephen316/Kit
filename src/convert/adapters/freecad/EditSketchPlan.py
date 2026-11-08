# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping

from convert.adapters.freecad.EditExtScope import HasEditState
from convert.geometry.Formula.Arithmetic import (
    EvalFormula,
    IsLiteralFormula,
    ReadFormula,
)
from convert.geometry.Formula.FormulaUnits import MatchQuantity
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import (
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import Sketch
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.records.RecordParameter import Parameter
from interchange.serialization.WireData import ValidateWireMap

# the versioned sketch binding identifies archives with independently verifiable edit semantics
KSketchEditBinding = "KitEditableSketchV1"

# these relation families have direct and independently measurable native solver semantics
KEditableSketchRules = frozenset(
    {
        "horizontal",
        "vertical",
        "coincident",
        "point_on_object",
        "distance",
        "distance_x",
        "distance_y",
        "angle",
        "radius",
        "diameter",
        "parallel",
        "perpendicular",
        "equal",
        "concentric",
        "tangent",
        "midpoint",
        "symmetric",
    }
)


# isolated sketches have no dependent bodies or unprojected source modeling operations
def IsSketchScope(Document: CadDocument) -> bool:
    if (
        Document.source.format_id != "fusion.f3d"
        or Document.units != UnitSystem.KMillimeter
        or Document.assembly is not None
        or Document.brep is not None
        or Document.bodies
        or Document.meshes
        or Document.selections
        or not Document.sketches
        or len(Document.configurations) != 1
        or len(Document.support_planes) != len(Document.sketches)
        or len(Document.feature_timeline) != len(Document.sketches)
        or any(
            Value.role != PayloadRole.KDocument or Value.format_id != "fusion.f3d"
            for Value in Document.brep_payloads
        )
        or any(Value.code != "fusion.history.partial" for Value in Document.diagnostics)
        or Document.metadata.get("freecad")
    ):
        return False
    Config = Document.configurations[0]
    Inventory = Document.metadata.get("fusion.body_inventory")
    return (
        Config.active
        and not (
            Config.parent_id
            or Config.overrides
            or Config.suppressed_feature_ids
            or Config.attributes
        )
        and isinstance(Inventory, Mapping)
        and Inventory.get("members") == ()
        and Document.metadata.get("fusion.history_groups") == ()
        and HasSketchHistory(Document)
    )


# each retained sketch step must account for one exact source history member
def HasSketchHistory(Document: CadDocument) -> bool:
    Entries = Document.metadata.get("fusion.history_entries")
    return (
        isinstance(Entries, tuple)
        and len(Entries) == len(Document.feature_timeline)
        and tuple(str(Value) for Value in Entries)
        == tuple(
            Origin.native_id
            for Value in Document.feature_timeline
            if (Origin := Value.provenance) is not None
            and Origin.adapter == "fusion.f3d"
        )
    )


# every marked sketch must own a supported independent native solver graph
def IsSketchStep(SketchValue: Sketch, StepValue: FeatureStep) -> bool:
    return (
        StepValue.kind == FeatureKind.KNative
        and StepValue.definition is None
        and StepValue.operation is None
        and not StepValue.input_feature_ids
        and HasEditState(StepValue)
        and not SketchValue.suppressed
        and not SketchValue.closed_profile_entity_ids
        and SketchValue.provenance is not None
        and SketchValue.provenance.adapter == "fusion.f3d"
        and SketchValue.parameter_ids == StepValue.parameter_ids
        and bool(SketchValue.constraints)
        and all(
            Value.kind in KEditableSketchRules and not Value.suppressed
            for Value in SketchValue.constraints
        )
        and all(
            isinstance(Value.geometry, (PointGeometry, LineGeometry, CircleGeometry))
            for Value in SketchValue.entities
        )
    )


# literal owned parameters allow dimensional edits without inventing source formulas
def IsSketchParam(ParamValue: Parameter, OwnerId: str) -> bool:
    Expression = ParamValue.expression
    if (
        ParamValue.owner_id != OwnerId
        or Expression is None
        or Expression.language != "fusion"
        or Expression.parameter_ids
    ):
        return False
    Formula = ReadFormula(Expression.source)
    if Formula is None or not IsLiteralFormula(Formula):
        return False
    Quantity = EvalFormula(Formula, {})
    return Quantity is not None and MatchQuantity(Quantity, ParamValue.value)


# the worksheet inventory must match the exact owned dimension records
def ReadSketchDims(
    SketchValue: Sketch, StepValue: FeatureStep, Parameters: Mapping[str, Parameter]
) -> dict[str, bool] | None:
    DimRules = {
        Value.parameter_id: Value.driving
        for Value in SketchValue.constraints
        if Value.parameter_id is not None
    }
    if (
        len(DimRules)
        != sum(Value.parameter_id is not None for Value in SketchValue.constraints)
        or set(DimRules) != set(SketchValue.parameter_ids)
        or any(
            ParamId not in Parameters
            or not IsSketchParam(Parameters[ParamId], StepValue.id)
            for ParamId in DimRules
        )
    ):
        return None
    return DimRules


# a complete source inventory prevents native edits from bypassing omitted modeling state
def ReadSketchPlan(Document: CadDocument) -> dict[str, bool] | None:
    if not IsSketchScope(Document):
        return None
    Steps = {Value.sketch_id: Value for Value in Document.feature_timeline}
    Frames = {Value.id: Value for Value in Document.support_planes}
    Parameters = {Value.id: Value for Value in Document.parameters}
    Result: dict[str, bool] = {}
    if (
        len(Steps) != len(Document.sketches)
        or len(Parameters) != len(Document.parameters)
        or set(Frames) != {Value.support_plane_id for Value in Document.sketches}
    ):
        return None
    for SketchValue in Document.sketches:
        StepValue = Steps.get(SketchValue.id)
        Plane = Frames[SketchValue.support_plane_id]
        if (
            StepValue is None
            or not IsSketchStep(SketchValue, StepValue)
            or Plane.support_selection_id is not None
            or Plane.offset_parameter_id is not None
        ):
            return None
        DimRules = ReadSketchDims(SketchValue, StepValue, Parameters)
        if DimRules is None or set(Result).intersection(DimRules):
            return None
        Result.update(DimRules)
    return Result if Result.keys() == Parameters.keys() else None


# writing uses the same typed sketch scope as reading a bound archive
def IsSketchWire(Manifest: Mapping[str, object]) -> bool:
    if Manifest.get("$type") != "CadDocument" or Manifest.get("brep") is not None:
        return False
    try:
        Document = CadDocument.from_dict(ValidateWireMap(Manifest))
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        return False
    return ReadSketchPlan(Document) is not None
