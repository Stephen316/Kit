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
    KSubtypeValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadScopeMut import (
    ReadScopeMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadTsplSurf import (
    ReadTsplSurf,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.NamedRules import (
    KNamedRules,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.ReadLeafMut import (
    ReadLeafMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubdataCodec import (
    ReadSubdataMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeFamily import (
    KScopeFamily,
    KSubtypeFamily,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeRules import (
    KSubtypeRules,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedCodecs import TypeBody
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.ReadBsCurve import (
    ReadBsCurveMut,
    ReadBsOptionMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.ReadBsSurface import (
    ReadSurfaceMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadNameMut import (
    ReadNameMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)


def ReadRuleMut(Cursor: FieldCursor, Grammar: KGrammarRule) -> KGrammarValue:
    if isinstance(Grammar, LeafRule):
        return ReadLeafMut(Cursor, Grammar.LeafKind)
    if isinstance(Grammar, FixedRule):
        NeedFieldMut(Cursor, Grammar.Token)
        return None
    if isinstance(Grammar, ChainRule):
        return tuple(ReadRuleMut(Cursor, Member) for Member in Grammar.Items)
    if isinstance(Grammar, RepeatRule):
        Count = ReadCountMut(Cursor, 4096)
        return tuple(ReadRuleMut(Cursor, Grammar.Member) for _ in range(Count))
    if isinstance(Grammar, GateRule):
        return ReadRuleMut(Cursor, Grammar.Member) if IsLogicalMut(Cursor) else None
    if isinstance(Grammar, CrossRule):
        return ReadCrossMut(Cursor, Grammar)
    if isinstance(Grammar, CallRule):
        return ReadCallMut(Cursor, Grammar.RuleName)
    return ReadChoiceMut(Cursor, Grammar)


def ReadCrossMut(Cursor: FieldCursor, Grammar: CrossRule) -> KGrammarValue:
    TrailCount = ReadCountMut(Cursor, 4096)
    LeadCount = ReadCountMut(Cursor, 4096)
    LeadItems = tuple(ReadRuleMut(Cursor, Grammar.Leader) for _ in range(LeadCount))
    TrailItems = tuple(ReadRuleMut(Cursor, Grammar.Trailer) for _ in range(TrailCount))
    return LeadItems, TrailItems


def ReadProbeMut(
    Cursor: FieldCursor, Grammar: PickRule | SwitchRule | PeekRule
) -> int | str:
    if isinstance(Grammar, PeekRule):
        if Cursor.Offset >= len(Cursor.Record.Tokens):
            raise ValueError("Truncated Fusion journal entity")
        return Cursor.Record.Tokens[Cursor.Offset][0]
    if isinstance(Grammar, PickRule):
        return ReadNameMut(Cursor) if Grammar.ProbeTag == 13 else ReadTextMut(Cursor)
    if Grammar.ProbeKind == "flag":
        return 1 if IsLogicalMut(Cursor) else 0
    return ReadLongMut(Cursor, 21 if Grammar.ProbeKind == "enum" else 4)


def ReadChoiceMut(
    Cursor: FieldCursor, Grammar: PickRule | SwitchRule | PeekRule
) -> ChoiceValue:
    ChoiceKey = ReadProbeMut(Cursor, Grammar)
    Fallback = None if isinstance(Grammar, PeekRule) else Grammar.Fallback
    Selected = next(
        (Member for OptionKey, Member in Grammar.Options if OptionKey == ChoiceKey),
        Fallback,
    )
    if Selected is None:
        raise ValueError(
            "Unsupported Fusion subtype grammar variant: " + str(ChoiceKey)
        )
    return ChoiceValue(ChoiceKey, ReadRuleMut(Cursor, Selected))


def ReadCallMut(Cursor: FieldCursor, RuleName: str) -> KGrammarValue:
    if RuleName in KScopeFamily:
        return ReadSubtypeMut(Cursor, KScopeFamily[RuleName])
    if RuleName in ("bs2", "bs3"):
        return ReadBsCurveMut(Cursor, 2 if RuleName == "bs2" else 3)
    if RuleName == "bs2option":
        return ReadBsOptionMut(Cursor)
    if RuleName == "bss":
        return ReadSurfaceMut(Cursor)
    if RuleName == "subdata":
        return ReadSubdataMut(Cursor)
    return ReadRuleMut(Cursor, KNamedRules[RuleName])


def ReadSubtypeMut(Cursor: FieldCursor, Family: str) -> KSubtypeValue:
    Scope = ReadScopeMut(Cursor, Family)
    if isinstance(Scope, SubtypeRef):
        return Scope
    if Scope == "t_spl_sur" and Family == "surface":
        return ReadTsplSurf(Cursor)
    if KSubtypeFamily.get(Scope) != Family or Scope not in KSubtypeRules:
        raise ValueError("Unsupported Fusion " + Family + " subtype: " + Scope)
    TreeValue = ReadRuleMut(Cursor, KSubtypeRules[Scope])
    Value = SubtypeNode(Scope, TypeBody(Scope, TreeValue))
    NeedFieldMut(Cursor, (16, None))
    return Value
