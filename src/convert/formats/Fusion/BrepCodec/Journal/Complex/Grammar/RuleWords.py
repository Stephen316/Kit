from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarRule import (
    CallRule,
    ChainRule,
    CrossRule,
    FixedRule,
    GateRule,
    KGrammarRule,
    LeafRule,
    PickRule,
    RepeatRule,
    SwitchRule,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def Chain(*Items: KGrammarRule) -> ChainRule:
    return ChainRule(Items)


def Repeat(Member: KGrammarRule) -> RepeatRule:
    return RepeatRule(Member)


def Gated(Member: KGrammarRule) -> GateRule:
    return GateRule(Member)


def Named(RuleName: str) -> CallRule:
    return CallRule(RuleName)


def Exact(Token: KAsmToken) -> FixedRule:
    return FixedRule(Token)


def Cross(Leader: KGrammarRule, Trailer: KGrammarRule) -> CrossRule:
    return CrossRule(Leader, Trailer)


def Picks(
    ProbeTag: int,
    Options: dict[str, KGrammarRule],
    Fallback: KGrammarRule | None = None,
) -> PickRule:
    return PickRule(ProbeTag, tuple(Options.items()), Fallback)


def Branch(
    ProbeKind: str,
    Options: dict[int, KGrammarRule],
    Fallback: KGrammarRule | None = None,
) -> SwitchRule:
    return SwitchRule(ProbeKind, tuple(Options.items()), Fallback)


KIntLeaf = LeafRule("int")
KRealLeaf = LeafRule("real")
KEnumLeaf = LeafRule("enum")
KFlagLeaf = LeafRule("flag")
KBoundLeaf = LeafRule("bound")
KPointLeaf = LeafRule("point")
KVectorLeaf = LeafRule("vector")
KTextLeaf = LeafRule("text")
KBoundPair = ChainRule((KBoundLeaf, KBoundLeaf))
KBoundQuad = ChainRule((KBoundLeaf, KBoundLeaf, KBoundLeaf, KBoundLeaf))
KRealArray = RepeatRule(KRealLeaf)
KSurfaceCall = CallRule("surface")
KCurveCall = CallRule("curve")
KOptionCall = CallRule("bs2option")
KPlaneCall = CallRule("bs2")
KSpaceCall = CallRule("bs3")
KTailCall = CallRule("tail")
KContextCall = CallRule("context")
