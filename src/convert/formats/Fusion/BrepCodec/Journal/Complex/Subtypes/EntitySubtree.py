from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


# the entity subtree contract needs a shared interpretation so nested spline and surface records retain their relationships
def EntitySubtree(Entity: KJournalEntity) -> KGrammarValue:
    if isinstance(Entity, SplineNode):
        return Entity.Surface
    if isinstance(Entity, (IntcurveNode, PcurveNode, TcoedgeNode)):
        return Entity.Curve
    return None


# swap subtree needs an explicit validity boundary so nested spline and surface records retain their relationships
def SwapSubtree(Entity: KJournalEntity, Value: KGrammarValue) -> KJournalEntity:
    if isinstance(Value, (SubtypeNode, SubtypeRef, TsplineSurf)):
        if isinstance(Entity, SplineNode):
            return ReplaceValue(Entity, Surface=Value)
        if isinstance(Entity, (IntcurveNode, PcurveNode)):
            return ReplaceValue(Entity, Curve=Value)
    if isinstance(Entity, PcurveNode) and Value is None:
        return ReplaceValue(Entity, Curve=Value)
    if isinstance(Entity, TcoedgeNode):
        return ReplaceValue(Entity, Curve=Value)
    if Value is not None:
        raise ValueError("Fusion entity cannot carry a subtype tree")
    return Entity
