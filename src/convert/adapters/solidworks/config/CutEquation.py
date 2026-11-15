from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.sketch.InlineSketch import InlineRead


# an equation can refer only to a dimension in one of these reached sketch bodies
@Dataclass(frozen=True, slots=True)
class ConfigSketch:
    SketchIndex: int
    Start: int
    EndOffset: int
    NextIndex: int
    SketchData: InlineRead


# the authored token and slot corroborate a concrete saved length dimension
@Dataclass(frozen=True, slots=True)
class EquationDim:
    LabelValue: str
    ParamName: str
    SketchName: str
    SketchIndex: int
    DimensionSlot: int
    DimensionId: int
    Metres: float
    Start: int
    EndOffset: int
    SlotOffset: int


# a reached equation retains the ordered arguments and its enclosing allocation
@Dataclass(frozen=True, slots=True)
class CutEquation:
    SourceText: str
    ObjectIndex: int
    Start: int
    EndOffset: int
    TextStart: int
    TextEnd: int
    Target: EquationDim
    OuterTerm: EquationDim
    InnerTerm: EquationDim
