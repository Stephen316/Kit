from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# leaf rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class LeafRule:
    LeafKind: str


# fixed rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class FixedRule:
    Token: KAsmToken


# call rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class CallRule:
    RuleName: str


# chain rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class ChainRule:
    Items: tuple["KGrammarRule", ...]


# repeat rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class RepeatRule:
    Member: "KGrammarRule"


# gate rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class GateRule:
    Member: "KGrammarRule"


# the rule operation needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class CrossRule:
    Leader: "KGrammarRule"
    Trailer: "KGrammarRule"


# pick rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class PickRule:
    ProbeTag: int
    Options: tuple[tuple[str, "KGrammarRule"], ...]
    Fallback: Union["KGrammarRule", None] = None


# switch rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class SwitchRule:
    ProbeKind: str
    Options: tuple[tuple[int, "KGrammarRule"], ...]
    Fallback: Union["KGrammarRule", None] = None


# peek rule needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class PeekRule:
    Options: tuple[tuple[int, "KGrammarRule"], ...]


# the grammar rule shape must stay shared so journal grammar decoding uses one contract for compatible values
KGrammarRule: TypeAlias = Union[
    LeafRule,
    FixedRule,
    CallRule,
    ChainRule,
    RepeatRule,
    GateRule,
    CrossRule,
    PickRule,
    SwitchRule,
    PeekRule,
]
