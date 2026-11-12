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
