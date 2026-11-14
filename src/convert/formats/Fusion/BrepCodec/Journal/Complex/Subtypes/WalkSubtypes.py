from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    KSubtypeEntry,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedRecord import (
    KRecordTypes,
    RebuildRecord,
    RecordParts,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


def WalkSubtypes(Value: KGrammarValue) -> tuple[KSubtypeEntry, ...]:
    if isinstance(Value, SubtypeNode):
        return (Value, *WalkSubtypes(Value.Body))
    if isinstance(Value, TsplineSurf):
        return (Value, *WalkSubtypes(Value.Subtrans))
    if isinstance(Value, (SubtypeRef, SubtransNode)):
        return (Value,)
    if isinstance(Value, ChoiceValue):
        return WalkSubtypes(Value.Body)
    if isinstance(Value, KRecordTypes):
        return WalkSubtypes(RecordParts(Value))
    if type(Value) is tuple:
        return tuple(Found for Element in Value for Found in WalkSubtypes(Element))
    return ()


def DefinedName(Value: KSubtypeEntry) -> str:
    if isinstance(Value, SubtypeNode):
        return Value.SubtypeName
    if isinstance(Value, TsplineSurf):
        return "t_spl_sur"
    if isinstance(Value, SubtransNode):
        return "t_spl_subtrans_object"
    return "ref"


def WithSubtrans(Value: TsplineSurf, Subtrans: KGrammarValue) -> TsplineSurf:
    if not isinstance(Subtrans, (SubtransNode, SubtypeRef)):
        raise ValueError("Fusion T-spline surface lost its subtransform scope")
    return ReplaceValue(Value, Subtrans=Subtrans)


def MapSubtypes(Value: KGrammarValue, Mapping: dict[int, int]) -> KGrammarValue:
    if isinstance(Value, SubtypeNode):
        return SubtypeNode(Value.SubtypeName, MapSubtypes(Value.Body, Mapping))
    if isinstance(Value, TsplineSurf):
        return WithSubtrans(Value, MapSubtypes(Value.Subtrans, Mapping))
    if isinstance(Value, SubtypeRef):
        if Value.Index not in Mapping:
            raise ValueError("Fusion subtype reference precedes every definition")
        return SubtypeRef(Value.Family, Mapping[Value.Index])
    if isinstance(Value, ChoiceValue):
        return ChoiceValue(Value.ChoiceKey, MapSubtypes(Value.Body, Mapping))
    if isinstance(Value, KRecordTypes):
        Parts = RecordParts(Value)
        return RebuildRecord(
            Value, tuple(MapSubtypes(Element, Mapping) for Element in Parts)
        )
    if type(Value) is tuple:
        return tuple(MapSubtypes(Element, Mapping) for Element in Value)
    return Value
