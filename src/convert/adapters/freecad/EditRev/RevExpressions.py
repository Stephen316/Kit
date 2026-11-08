# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Mapping

from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.FormulaSheet.FormulaPlans import IsFormulaAlias


# one canonical expression graph preserves signed and centered revolutions
def RevExpressions(
    PlanValue: EditRevolve, Aliases: Mapping[str, str]
) -> tuple[tuple[str, str], ...]:
    Along = Aliases.get(PlanValue.AngleParamId)
    if Along is None or not IsFormulaAlias(Along):
        return ()
    AlongRef = f"Parameters.{Along}"
    if PlanValue.AgainstParamId is None:
        return (("Angle", AlongRef),)
    Against = Aliases.get(PlanValue.AgainstParamId)
    if Against is None or not IsFormulaAlias(Against) or Against == Along:
        return ()
    if PlanValue.AngleScale != 1.0:
        return (("Angle", f"{AlongRef} * {PlanValue.AngleScale:g}"),)
    AgainstRef = f"Parameters.{Against}"
    AxisValue = PlanValue.AxisDirection
    AxisText = f"{AxisValue.x:.17g}; {AxisValue.y:.17g}; {AxisValue.z:.17g}"
    Placement = (
        "placement(vector(0 mm; 0 mm; 0 mm); "
        f"rotation(vector({AxisText}); ({AlongRef} - {AgainstRef}) / 2))"
    )
    return (("Angle", f"{AlongRef} + {AgainstRef}"), ("Placement", Placement))
