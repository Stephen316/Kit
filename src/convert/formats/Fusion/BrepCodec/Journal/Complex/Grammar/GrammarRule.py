from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


@MakeDataClass(frozen=True, slots=True)
class LeafRule:
    LeafKind: str


@MakeDataClass(frozen=True, slots=True)
class FixedRule:
    Token: KAsmToken


@MakeDataClass(frozen=True, slots=True)
class CallRule:
    RuleName: str


@MakeDataClass(frozen=True, slots=True)
class ChainRule:
    Items: tuple["KGrammarRule", ...]


@MakeDataClass(frozen=True, slots=True)
class RepeatRule:
    Member: "KGrammarRule"


@MakeDataClass(frozen=True, slots=True)
class GateRule:
    Member: "KGrammarRule"


@MakeDataClass(frozen=True, slots=True)
class CrossRule:
    Leader: "KGrammarRule"
    Trailer: "KGrammarRule"


@MakeDataClass(frozen=True, slots=True)
class PickRule:
    ProbeTag: int
    Options: tuple[tuple[str, "KGrammarRule"], ...]
    Fallback: Union["KGrammarRule", None] = None


@MakeDataClass(frozen=True, slots=True)
class SwitchRule:
    ProbeKind: str
    Options: tuple[tuple[int, "KGrammarRule"], ...]
    Fallback: Union["KGrammarRule", None] = None


@MakeDataClass(frozen=True, slots=True)
class PeekRule:
    Options: tuple[tuple[int, "KGrammarRule"], ...]


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
