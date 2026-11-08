# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from ast import dump as DumpAst

from convert.geometry.Formula.Arithmetic import Formula


# matching operator trees tolerates formatting without accepting altered aliases or arithmetic
def IsSameFormula(Expected: Formula, Saved: Formula) -> bool:
    return DumpAst(Expected.RootValue) == DumpAst(Saved.RootValue) and tuple(
        Operand.TextValue if Operand.Quantity is None else Operand.Quantity
        for Operand in Expected.Atoms
    ) == tuple(
        Operand.TextValue if Operand.Quantity is None else Operand.Quantity
        for Operand in Saved.Atoms
    )
