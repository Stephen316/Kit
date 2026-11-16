from math import isclose as IsClose

from convert.adapters.solidworks.Config.CutEqRefs import OpenEqObject, ReadEqDim
from convert.adapters.solidworks.Config.CutEquation import (
    ConfigSketch,
    CutEquation,
    EquationDim,
)
from convert.adapters.solidworks.Container.Archive import KObjectRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# operator and number tokens carry distinct typed layouts and ordered source regions
def ReadEqToken(Cursor: ArchiveCursor, Token: str, IsNumber: bool = False) -> None:
    ClassName = "moRelValue_c" if IsNumber else "moRelOperator_c"
    _ = OpenEqObject(Cursor, ClassName)
    RequireArch(Cursor.ReadText(), Token, "saved centering token")
    TypeCode, FirstPos, LastPos, RoleValue = Cursor.ReadInts("<4i")
    RequireArch((TypeCode, RoleValue), (8, 2 if IsNumber else 3), "equation token type")
    RequireArch(0 <= FirstPos < LastPos, True, "ordered equation token positions")


# each equation side must return to the same owning relation object
def ReadEqSideEnd(Cursor: ArchiveCursor, Owner: int, SideValue: int) -> str:
    LabelValue = Cursor.ReadText()
    RequireArch(Cursor.ReadInts("<2i"), (0, SideValue), "saved equation side state")
    _, _, Parent = Cursor.TakePointer(
        ("moRelation_c",), KObjectRefKind, CompactOnly=True
    )
    RequireArch(Parent, Owner, "equation side owns its relation")
    return LabelValue


# a centering right side consumes its full ordered token and owner chain
def ReadEqRight(
    Cursor: ArchiveCursor, Sketches: dict[int, ConfigSketch], Owner: int
) -> tuple[EquationDim, EquationDim, str]:
    _ = OpenEqObject(Cursor, "moRelEquationSide_c")
    RequireArch(Cursor.ReadInts("<H"), (8,), "eight centering expression tokens")
    ReadEqToken(Cursor, "=")
    ReadEqToken(Cursor, "(")
    OuterTerm = ReadEqDim(Cursor, Sketches)
    ReadEqToken(Cursor, "-")
    InnerTerm = ReadEqDim(Cursor, Sketches)
    ReadEqToken(Cursor, ")")
    ReadEqToken(Cursor, "/")
    ReadEqToken(Cursor, "2", True)
    SideText = ReadEqSideEnd(Cursor, Owner, 0)
    RequireArch(
        SideText,
        f" = ({OuterTerm.LabelValue} - {InnerTerm.LabelValue}) / 2",
        "right side text agrees with its ordered handles",
    )
    return OuterTerm, InnerTerm, SideText


# the lhs and both right operands must form one evaluated centering dependency
def CheckEqValue(
    Target: EquationDim, OuterTerm: EquationDim, InnerTerm: EquationDim
) -> None:
    RequireArch(
        (Target.SketchIndex, Target.SketchName),
        (InnerTerm.SketchIndex, InnerTerm.SketchName),
        "target and cut size are in one sketch",
    )
    RequireArch(
        OuterTerm.SketchIndex != InnerTerm.SketchIndex, True, "outer source sketch"
    )
    RequireArch(
        Target.DimensionSlot != InnerTerm.DimensionSlot,
        True,
        "distinct target and cut size",
    )
    Expected = (OuterTerm.Metres - InnerTerm.Metres) / 2
    RequireArch(
        IsClose(Target.Metres, Expected, rel_tol=0, abs_tol=1e-12),
        True,
        "cached centering value agrees with authored equation",
    )


# a relation is retained only when both sides and its terminal label agree
def ReadCutEq(
    Cursor: ArchiveCursor, Sketches: dict[int, ConfigSketch], Sequence: int
) -> CutEquation:
    Start = Cursor.Offset
    Owner = OpenEqObject(Cursor, "moRelation_c")
    TextStart = Cursor.Offset
    SourceText = Cursor.ReadText()
    TextEnd = Cursor.Offset
    RequireArch(Cursor.ReadInts("<Hi"), (512, 0), "saved active equation state")
    _ = OpenEqObject(Cursor, "moRelEquationSide_c")
    RequireArch(Cursor.ReadInts("<H"), (1,), "one equation target")
    Target = ReadEqDim(Cursor, Sketches)
    LeftText = ReadEqSideEnd(Cursor, Owner, 1)
    RequireArch(LeftText, Target.LabelValue, "equation lhs agrees with its handle")
    OuterTerm, InnerTerm, RightText = ReadEqRight(Cursor, Sketches, Owner)
    RequireArch(
        SourceText, LeftText + RightText, "full equation agrees with its saved sides"
    )
    RequireArch(Cursor.ReadInts("<2i"), (0, Sequence), "ordered saved relation index")
    RequireArch(Cursor.ReadText(), "uuUNDEFINED", "native default relation label")
    RequireArch(Cursor.ReadInts("<3i"), (0, 0, 0), "guarded relation return")
    CheckEqValue(Target, OuterTerm, InnerTerm)
    return CutEquation(
        SourceText,
        Owner,
        Start,
        Cursor.Offset,
        TextStart,
        TextEnd,
        Target,
        OuterTerm,
        InnerTerm,
    )
