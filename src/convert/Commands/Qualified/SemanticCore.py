from collections.abc import Mapping
from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from typing import cast as CastValue

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumBase import WireEnum


# qualified geometry comparisons must preserve semantics while excluding incidental provenance and annotations
def SemanticCore(Value: object) -> object:
    if isinstance(Value, WireEnum):
        return SemanticCore(Value.value)
    if IsDataClass(Value) and not isinstance(Value, type):
        Records: list[tuple[str, object]] = []
        for Field in DataFields(Value):
            if Field.name in ("attributes", "provenance") or (
                isinstance(Value, CadDocument) and Field.name in ("source", "metadata")
            ):
                continue
            Member: object = getattr(Value, Field.name)
            if isinstance(Value, CadDocument) and Field.name == "feature_timeline":

                # timeline equality must ignore storage order while preserving declared feature execution order
                Member = tuple(
                    sorted(Value.feature_timeline, key=lambda Feature: Feature.order)
                )
            Records.append((Field.name, SemanticCore(Member)))
        return type(Value), tuple(Records)
    if isinstance(Value, Mapping):
        return {
            KeyValue: SemanticCore(Member)
            for KeyValue, Member in CastValue(Mapping[object, object], Value).items()
        }
    if isinstance(Value, (tuple, list)):
        return type(CastValue(object, Value)), tuple(
            SemanticCore(Member)
            for Member in CastValue(tuple[object, ...] | list[object], Value)
        )
    if isinstance(Value, (set, frozenset)):
        return type(CastValue(object, Value)), frozenset(
            SemanticCore(Member)
            for Member in CastValue(set[object] | frozenset[object], Value)
        )
    return type(Value), Value
