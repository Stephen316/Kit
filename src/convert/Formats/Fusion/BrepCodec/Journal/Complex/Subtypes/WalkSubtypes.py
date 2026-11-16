from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    KSubtypeEntry,
    SubtypeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedRecord import (
    KRecordTypes,
    RebuildRecord,
    RecordParts,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.Formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


# the walk subtypes contract needs a shared interpretation so nested spline and surface records retain their relationships
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


# the defined name contract needs a shared interpretation so nested spline and surface records retain their relationships
def DefinedName(Value: KSubtypeEntry) -> str:
    if isinstance(Value, SubtypeNode):
        return Value.SubtypeName
    if isinstance(Value, TsplineSurf):
        return "t_spl_sur"
    if isinstance(Value, SubtransNode):
        return "t_spl_subtrans_object"
    return "ref"


# with subtrans needs an explicit validity boundary so nested spline and surface records retain their relationships
def WithSubtrans(Value: TsplineSurf, Subtrans: KGrammarValue) -> TsplineSurf:
    if not isinstance(Subtrans, (SubtransNode, SubtypeRef)):
        raise ValueError("Fusion T-spline surface lost its subtransform scope")
    return ReplaceValue(Value, Subtrans=Subtrans)


# map subtypes must resolve unambiguously so nested spline and surface records retain their relationships
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
