from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarRule import (
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
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the chain contract needs a shared interpretation so nested geometry retains unambiguous record boundaries
def Chain(*Items: KGrammarRule) -> ChainRule:
    return ChainRule(Items)


# the repeat contract needs a shared interpretation so nested geometry retains unambiguous record boundaries
def Repeat(Member: KGrammarRule) -> RepeatRule:
    return RepeatRule(Member)


# the gated contract needs a shared interpretation so nested geometry retains unambiguous record boundaries
def Gated(Member: KGrammarRule) -> GateRule:
    return GateRule(Member)


# the named contract needs a shared interpretation so nested geometry retains unambiguous record boundaries
def Named(RuleName: str) -> CallRule:
    return CallRule(RuleName)


# the exact contract needs a shared interpretation so nested geometry retains unambiguous record boundaries
def Exact(Token: KAsmToken) -> FixedRule:
    return FixedRule(Token)


# cross needs one geometric convention so nested geometry retains unambiguous record boundaries
def Cross(Leader: KGrammarRule, Trailer: KGrammarRule) -> CrossRule:
    return CrossRule(Leader, Trailer)


# picks must resolve unambiguously so nested geometry retains unambiguous record boundaries
def Picks(
    ProbeTag: int,
    Options: dict[str, KGrammarRule],
    Fallback: KGrammarRule | None = None,
) -> PickRule:
    return PickRule(ProbeTag, tuple(Options.items()), Fallback)


# the branch contract needs a shared interpretation so nested geometry retains unambiguous record boundaries
def Branch(
    ProbeKind: str,
    Options: dict[int, KGrammarRule],
    Fallback: KGrammarRule | None = None,
) -> SwitchRule:
    return SwitchRule(ProbeKind, tuple(Options.items()), Fallback)


# int leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KIntLeaf = LeafRule("int")

# real leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KRealLeaf = LeafRule("real")

# enum leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KEnumLeaf = LeafRule("enum")

# flag leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KFlagLeaf = LeafRule("flag")

# bound leaf needs one explicit bound so journal grammar decoding cannot accept inconsistent resource or layout limits
KBoundLeaf = LeafRule("bound")

# point leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KPointLeaf = LeafRule("point")

# vector leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KVectorLeaf = LeafRule("vector")

# text leaf must remain consistent across callers so nested geometry retains unambiguous record boundaries
KTextLeaf = LeafRule("text")

# bound pair needs one explicit bound so journal grammar decoding cannot accept inconsistent resource or layout limits
KBoundPair = ChainRule((KBoundLeaf, KBoundLeaf))

# bound quad needs one explicit bound so journal grammar decoding cannot accept inconsistent resource or layout limits
KBoundQuad = ChainRule((KBoundLeaf, KBoundLeaf, KBoundLeaf, KBoundLeaf))

# real array must remain consistent across callers so nested geometry retains unambiguous record boundaries
KRealArray = RepeatRule(KRealLeaf)

# surface call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KSurfaceCall = CallRule("surface")

# curve call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KCurveCall = CallRule("curve")

# option call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KOptionCall = CallRule("bs2option")

# plane call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KPlaneCall = CallRule("bs2")

# space call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KSpaceCall = CallRule("bs3")

# tail call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KTailCall = CallRule("tail")

# context call must remain consistent across callers so nested geometry retains unambiguous record boundaries
KContextCall = CallRule("context")
