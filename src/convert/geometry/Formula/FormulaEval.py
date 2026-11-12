from ast import Add, BinOp, Div, Mult, Name, Sub, UAdd, UnaryOp, USub
from ast import expr as ExprNode, operator as OperatorNode
from collections.abc import Mapping
from math import isfinite as IsFinite

from convert.geometry.Formula.FormulaTokens import FormulaAtom
from convert.geometry.Formula.FormulaUnits import GetQuantity, KQuantity
from interchange.records.RecordParameter import ParameterValue


# operations on dimensions reject misleading arithmetic across incompatible units
def ApplyOperator(
    Operator: OperatorNode, LeftValue: KQuantity, RightValue: KQuantity
) -> KQuantity:
    First, FirstKind = LeftValue
    Second, SecondKind = RightValue
    if isinstance(Operator, (Add, Sub)):
        if FirstKind != SecondKind:
            raise ValueError("formula addition requires matching dimensions")
        Result = First + Second if isinstance(Operator, Add) else First - Second
        Dimension = FirstKind
    elif isinstance(Operator, Mult):
        Result = First * Second
        Dimension = (FirstKind[0] + SecondKind[0], FirstKind[1] + SecondKind[1])
    elif isinstance(Operator, Div):
        Result = First / Second
        Dimension = (FirstKind[0] - SecondKind[0], FirstKind[1] - SecondKind[1])
    else:
        raise ValueError("unsupported formula operator")
    if not IsFinite(Result) or max(map(abs, Dimension)) > 8:
        raise ValueError("formula arithmetic exceeds the supported range")
    return Result, Dimension


# interpreting only explicit arithmetic nodes keeps source text from executing code
def EvalNode(
    NodeValue: ExprNode,
    Atoms: tuple[FormulaAtom, ...],
    Values: Mapping[str, ParameterValue],
) -> KQuantity:
    if isinstance(NodeValue, BinOp):
        return ApplyOperator(
            NodeValue.op,
            EvalNode(NodeValue.left, Atoms, Values),
            EvalNode(NodeValue.right, Atoms, Values),
        )
    if isinstance(NodeValue, UnaryOp) and isinstance(NodeValue.op, (UAdd, USub)):
        Magnitude, Dimension = EvalNode(NodeValue.operand, Atoms, Values)
        return (-Magnitude if isinstance(NodeValue.op, USub) else Magnitude, Dimension)
    if isinstance(NodeValue, Name):
        AtomValue = Atoms[int(NodeValue.id[7:])]
        if AtomValue.Quantity is not None:
            return AtomValue.Quantity
        Quantity = GetQuantity(Values[AtomValue.TextValue])
        if Quantity is not None:
            return Quantity
    raise ValueError("unsupported formula value")
