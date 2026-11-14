from collections.abc import Iterable
from itertools import chain as ChainItems

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarRule import (
    CallRule,
    ChainRule,
    CrossRule,
    FixedRule,
    GateRule,
    KGrammarRule,
    LeafRule,
    PeekRule,
    PickRule,
    RepeatRule,
    SwitchRule,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeRefScope import (
    MakeRefScope,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeTsplSurf import (
    MakeTsplSurf,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.MakeLeaf import MakeLeaf
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.NamedRules import (
    KNamedRules,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubdataCodec import (
    MakeSubdata,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeFamily import (
    KScopeFamily,
    KSubtypeFamily,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeRules import (
    KSubtypeRules,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedCodecs import TreeBody
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.MakeBsCurve import (
    MakeBsCurve,
    MakeBsOption,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.MakeBsSurface import (
    MakeBsSurface,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def JoinTokens(Groups: Iterable[tuple[KAsmToken, ...]]) -> tuple[KAsmToken, ...]:
    return tuple(ChainItems.from_iterable(Groups))


def NeedTuple(Value: KGrammarValue, Length: int | None) -> tuple[KGrammarValue, ...]:
    if type(Value) is not tuple or (Length is not None and len(Value) != Length):
        raise ValueError("Fusion grammar sequence disagrees with its rule")
    return Value


def MakeRule(Grammar: KGrammarRule, Value: KGrammarValue) -> tuple[KAsmToken, ...]:
    if isinstance(Grammar, LeafRule):
        return MakeLeaf(Grammar.LeafKind, Value)
    if isinstance(Grammar, FixedRule):
        if Value is not None:
            raise ValueError("Fusion fixed grammar field cannot carry a value")
        return (Grammar.Token,)
    if isinstance(Grammar, ChainRule):
        Members = NeedTuple(Value, len(Grammar.Items))
        return JoinTokens(map(MakeRule, Grammar.Items, Members))
    if isinstance(Grammar, RepeatRule):
        Members = NeedTuple(Value, None)
        Tokens = JoinTokens(MakeRule(Grammar.Member, Element) for Element in Members)
        return ((4, len(Members)), *Tokens)
    if isinstance(Grammar, GateRule):
        if Value is None:
            return ((11, None),)
        return ((10, None), *MakeRule(Grammar.Member, Value))
    if isinstance(Grammar, CrossRule):
        return MakeCross(Grammar, Value)
    if isinstance(Grammar, CallRule):
        return MakeCall(Grammar.RuleName, Value)
    return MakeChoice(Grammar, Value)


def MakeCross(Grammar: CrossRule, Value: KGrammarValue) -> tuple[KAsmToken, ...]:
    LeadItems, TrailItems = (
        NeedTuple(Element, None) for Element in NeedTuple(Value, 2)
    )
    return (
        (4, len(TrailItems)),
        (4, len(LeadItems)),
        *JoinTokens(MakeRule(Grammar.Leader, Element) for Element in LeadItems),
        *JoinTokens(MakeRule(Grammar.Trailer, Element) for Element in TrailItems),
    )


def MakeProbe(
    Grammar: PickRule | SwitchRule | PeekRule, ChoiceKey: int | str
) -> tuple[KAsmToken, ...]:
    if isinstance(Grammar, PeekRule):
        return ()
    if isinstance(Grammar, PickRule):
        if type(ChoiceKey) is not str:
            raise ValueError("Fusion grammar name choice requires text")
        return ((Grammar.ProbeTag, ChoiceKey),)
    if type(ChoiceKey) is not int:
        raise ValueError("Fusion grammar switch choice requires an integer")
    if Grammar.ProbeKind == "flag":
        if ChoiceKey not in (0, 1):
            raise ValueError("Fusion grammar logical choice must be zero or one")
        return ((10 if ChoiceKey else 11, None),)
    return ((21 if Grammar.ProbeKind == "enum" else 4, ChoiceKey),)


def MakeChoice(
    Grammar: PickRule | SwitchRule | PeekRule, Value: KGrammarValue
) -> tuple[KAsmToken, ...]:
    if not isinstance(Value, ChoiceValue):
        raise ValueError("Fusion grammar choice requires a choice value")
    Fallback = None if isinstance(Grammar, PeekRule) else Grammar.Fallback
    Selected = next(
        (
            Member
            for OptionKey, Member in Grammar.Options
            if OptionKey == Value.ChoiceKey
        ),
        Fallback,
    )
    if Selected is None:
        raise ValueError("Unsupported Fusion subtype grammar variant")
    return (*MakeProbe(Grammar, Value.ChoiceKey), *MakeRule(Selected, Value.Body))


def MakeCall(RuleName: str, Value: KGrammarValue) -> tuple[KAsmToken, ...]:
    if RuleName in KScopeFamily:
        return MakeScope(KScopeFamily[RuleName], Value)
    if RuleName in ("bs2", "bs3") and isinstance(Value, BsCurve):
        return MakeBsCurve(Value, 2 if RuleName == "bs2" else 3)
    if RuleName == "bs2option" and (Value is None or isinstance(Value, BsCurve)):
        return MakeBsOption(Value)
    if RuleName == "bss" and isinstance(Value, BsSurface):
        return MakeBsSurface(Value)
    if RuleName == "subdata":
        return MakeSubdata(Value)
    if RuleName in KNamedRules:
        return MakeRule(KNamedRules[RuleName], Value)
    raise ValueError("Fusion grammar value disagrees with its rule: " + RuleName)


def MakeScope(Family: str, Value: KGrammarValue) -> tuple[KAsmToken, ...]:
    if isinstance(Value, TsplineSurf) and Family == "surface":
        return MakeTsplSurf(Value)
    if isinstance(Value, SubtypeRef):
        return MakeRefScope(Value, Family)
    if (
        not isinstance(Value, SubtypeNode)
        or KSubtypeFamily.get(Value.SubtypeName) != Family
        or Value.SubtypeName not in KSubtypeRules
    ):
        raise ValueError("Fusion subtype value disagrees with its " + Family + " scope")
    NameText = Value.SubtypeName
    Payload = MakeRule(KSubtypeRules[NameText], TreeBody(NameText, Value.Body))
    return ((15, None), (13, NameText), *Payload, (16, None))
