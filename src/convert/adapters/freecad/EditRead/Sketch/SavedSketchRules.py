# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import SafeAction
from convert.adapters.freecad.EditRead.Sketch.RuleGeometry import CheckGeomRule
from convert.adapters.freecad.EditRead.Sketch.RuleMeasures import CheckDimRule
from convert.adapters.freecad.EditRead.Sketch.RuleOperands import RuleOperands
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import (
    ReadRuleRows,
    SavedRuleRow,
)
from convert.adapters.freecad.Native import NativeObject
from convert.adapters.freecad.Protocol import KRuleCodeByKind, KRuleValueKindByCode
from interchange.geometry.models.Sketch import Sketch, SketchEntity, SketchRelation
from interchange.records.RecordParameter import Parameter


# emitted rule names associate verified solver rows with exact original neutral relations
def AuthoredRules(Original: Sketch) -> dict[str, SketchRelation]:
    Result = {
        SafeAction(Value.id, "Constraint"): Value for Value in Original.constraints
    }
    if len(Result) != len(Original.constraints):
        raise ValueError(
            "FreeCAD editable sketch authored constraint names are ambiguous"
        )
    return Result


# generated incidence and block rows remain graph evidence but have no editable datum
def CheckStaticRow(Saved: SavedRuleRow) -> None:
    IsIncidence = Saved.NameValue.startswith("incidence_") and Saved.CodeValue == 1
    IsBlock = Saved.NameValue.startswith("fixed_") and Saved.CodeValue == 17
    if not (IsIncidence or IsBlock) or Saved.Value != Saved.ExpectedValue:
        raise ValueError("FreeCAD editable sketch generated constraint changed")


# static authored rules keep their solver value while active geometry must still solve
def CheckRuleValue(
    Relation: SketchRelation,
    Saved: SavedRuleRow,
    Original: Mapping[str, SketchEntity],
    Edited: Mapping[str, SketchEntity],
    Parameters: Mapping[str, Parameter],
) -> float | None:
    KindValue = Relation.kind
    CodeValue = 14 if KindValue == "midpoint" else KRuleCodeByKind.get(KindValue)
    if (
        Saved.CodeValue != CodeValue
        or Saved.Driving != Relation.driving
        or Saved.Active == Relation.suppressed
    ):
        raise ValueError("FreeCAD editable sketch authored constraint binding changed")
    if not Saved.Active:
        if Saved.Value != Saved.ExpectedValue:
            raise ValueError(
                "FreeCAD editable sketch inactive constraint value changed"
            )
        return None
    Operands = RuleOperands(Relation, Edited)
    if Saved.CodeValue in KRuleValueKindByCode:
        return CheckDimRule(Relation, Operands, Saved, Parameters)
    if Relation.parameter_id is not None or Saved.Value != Saved.ExpectedValue:
        raise ValueError("FreeCAD editable sketch geometric constraint value changed")
    CheckGeomRule(KindValue, RuleOperands(Relation, Original), Operands)
    return None


# changed sketch data is accepted only after its native graph and dimensional residuals agree
def CheckSavedRules(
    Native: NativeObject,
    ExpectedRules: Element,
    Original: Sketch,
    Edited: Sketch,
    Parameters: Mapping[str, Parameter],
) -> dict[str, float]:
    RuleRows = ReadRuleRows(Native, ExpectedRules)
    Authored = AuthoredRules(Original)
    if not Authored.keys() <= {Value.NameValue for Value in RuleRows}:
        raise ValueError(
            "FreeCAD editable sketch has a carrier only authored constraint"
        )
    OriginalEntities = {Value.id: Value for Value in Original.entities}
    EditedEntities = {Value.id: Value for Value in Edited.entities}
    if (
        Original.id != Edited.id
        or Original.constraints != Edited.constraints
        or OriginalEntities.keys() != EditedEntities.keys()
        or len(OriginalEntities) != len(Original.entities)
        or len(EditedEntities) != len(Edited.entities)
    ):
        raise ValueError("FreeCAD editable sketch constraint geometry identity changed")
    Measurements: dict[str, float] = {}
    for RowValue in RuleRows:
        Relation = Authored.get(RowValue.NameValue)
        if Relation is None:
            CheckStaticRow(RowValue)
            continue
        Value = CheckRuleValue(
            Relation, RowValue, OriginalEntities, EditedEntities, Parameters
        )
        if Value is not None:
            ParamId = Relation.parameter_id
            if ParamId is None or ParamId in Measurements:
                raise ValueError(
                    "FreeCAD editable sketch reference parameter binding is ambiguous"
                )
            Measurements[ParamId] = Value
    return Measurements
