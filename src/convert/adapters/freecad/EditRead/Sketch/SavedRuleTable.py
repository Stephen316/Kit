# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.XmlField import (
    EditAttr,
    EditChild,
    EditFloat,
    OnlyEditChild,
)
from convert.adapters.freecad.Native import NativeObject

# both legacy scalar slots and their modern redundant arrays bind geometry identity
KRuleIdentity = (
    "Name",
    "Type",
    "IsDriving",
    "IsActive",
    "First",
    "FirstPos",
    "Second",
    "SecondPos",
    "Third",
    "ThirdPos",
)

# default optional native fields may be omitted by a save without changing the rule
KRuleDefaults = {
    "MetaData": "",
    "Orientation": "0",
    "IsInVirtualSpace": "0",
    "IsVisible": "1",
}

# label placement is independent of solver semantics but still uses finite numbers
KRuleLabelFields = frozenset({"LabelDistance", "LabelPosition"})

# additional native fields can change solver semantics outside the verified subset
KRuleFields = (
    frozenset(KRuleIdentity)
    | frozenset(KRuleDefaults)
    | KRuleLabelFields
    | {
        "ElementIds",
        "ElementPositions",
        "Value",
    }
)


# verified rows preserve the exact authored identity and both persisted numeric values
@MakeDataClass(frozen=True, slots=True)
class SavedRuleRow:
    NameValue: str
    CodeValue: int
    Driving: bool
    Active: bool
    Value: float
    ExpectedValue: float


# matching rule templates accept only the optional formatting differences seen in native saves
def ReadRuleRow(Saved: Element, Expected: Element) -> SavedRuleRow:
    if (
        Saved.tag != "Constrain"
        or Expected.tag != "Constrain"
        or len(Saved)
        or len(Expected)
        or (Saved.text or "").strip()
        or set(Saved.attrib) - KRuleFields
        or any(
            EditAttr(Saved, Field) != EditAttr(Expected, Field)
            for Field in KRuleIdentity
        )
        or any(
            Saved.get(Field, Default) != Expected.get(Field, Default)
            for Field, Default in KRuleDefaults.items()
        )
    ):
        raise ValueError("FreeCAD editable sketch native constraint identity changed")
    Arrays = ("ElementIds", "ElementPositions")
    ExpectedSlots = len(Expected.get("ElementIds", "").split())
    if (ExpectedSlots > 3 or any(Field in Saved.attrib for Field in Arrays)) and any(
        EditAttr(Saved, Field).split() != EditAttr(Expected, Field).split()
        for Field in Arrays
    ):
        raise ValueError(
            "FreeCAD editable sketch native constraint element slots changed"
        )
    for Field in KRuleLabelFields & Saved.attrib.keys():
        _ = EditFloat(Saved, Field)
    return SavedRuleRow(
        EditAttr(Saved, "Name"),
        int(EditAttr(Saved, "Type")),
        EditAttr(Saved, "IsDriving") == "1",
        EditAttr(Saved, "IsActive") == "1",
        EditFloat(Saved, "Value"),
        EditFloat(Expected, "Value"),
    )


# stable count and order exclude introduced or replaced native solver rows
def ReadRuleRows(
    Native: NativeObject, ExpectedRules: Element
) -> tuple[SavedRuleRow, ...]:
    Saved = EditChild(
        Native, "Constraints", "Sketcher::PropertyConstraintList", "ConstraintList"
    )
    if ExpectedRules.tag == "ConstraintList":
        Expected = ExpectedRules
    elif (
        ExpectedRules.tag == "Property"
        and ExpectedRules.get("name") == "Constraints"
        and ExpectedRules.get("type") == "Sketcher::PropertyConstraintList"
    ):
        Expected = OnlyEditChild(ExpectedRules, "ConstraintList")
    else:
        raise ValueError("FreeCAD editable sketch expected constraints are invalid")
    if (
        len(Saved) != len(Expected)
        or Saved.get("count") != str(len(Saved))
        or Expected.get("count") != str(len(Expected))
    ):
        raise ValueError("FreeCAD editable sketch native constraint count changed")
    RuleRows = tuple(
        ReadRuleRow(Value, Template)
        for Value, Template in zip(Saved, Expected, strict=True)
    )
    if any(not Value.NameValue for Value in RuleRows) or len(
        {Value.NameValue for Value in RuleRows}
    ) != len(RuleRows):
        raise ValueError(
            "FreeCAD editable sketch native constraint names are ambiguous"
        )
    return RuleRows
