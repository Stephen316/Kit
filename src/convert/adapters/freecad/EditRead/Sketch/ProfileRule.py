# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Mapping

from convert.adapters.freecad.Archive import ConstraintsProp, ParamCatalog
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import ReadRuleRows
from convert.adapters.freecad.EditRead.Sketch.SavedSketchRules import CheckStaticRow
from convert.adapters.freecad.Native import NativeObject


# the selected circle center must retain its single generated native solver binding
def CheckProfileRow(
    Native: NativeObject,
    SketchData: Mapping[str, object],
    Indices: dict[str, int],
    CircleId: str,
    CenterId: str,
) -> None:
    Template, Expressions, Dependencies, Diagnostics = ConstraintsProp(
        SketchData, Indices, ParamCatalog([]), IncludeIncidence=True
    )
    if (
        Expressions
        or Dependencies
        or Diagnostics
        or len(Template) != 1
        or len(Template[0]) != 1
    ):
        raise ValueError(
            "FreeCAD editable profile has an invalid source constraint graph"
        )
    CircleIndex, CenterIndex = Indices[CircleId], Indices[CenterId]
    Expected = {
        "Name": f"incidence_{CircleIndex}_3",
        "Type": "1",
        "IsDriving": "1",
        "IsActive": "1",
        "First": str(CircleIndex),
        "FirstPos": "3",
        "Second": str(CenterIndex),
        "SecondPos": "1",
        "Third": "-2000",
        "ThirdPos": "0",
    }
    if any(Template[0][0].get(Field) != Value for Field, Value in Expected.items()):
        raise ValueError("FreeCAD editable profile source center binding disagrees")
    (RowValue,) = ReadRuleRows(Native, Template)
    CheckStaticRow(RowValue)
