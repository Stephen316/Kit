from collections.abc import Mapping
from re import Match, compile as CompilePattern
from typing import cast as CastValue

from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

KUuidPattern = CompilePattern(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
KNumberUnit = CompilePattern(r"(-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?) (mm|deg)")


def NativeSummary(Value: DocumentModel) -> object:
    Segments = tuple(
        (Segment.Metadata.Header.Segment, Segment.Records) for Segment in Value.Segments
    )
    return EncodeState((Segments, Value.Bodies, Value.Materials))


def NormalState(
    Value: object, Identities: dict[str, str], FieldName: str = ""
) -> object:
    if FieldName in ("Created", "Updated", "SavedAt", "AuthoredMicros"):
        return "native provenance"
    if isinstance(Value, str):
        if FieldName in ("ClassGuid", "BaseGuid"):
            return Value.upper()
        return NormalText(Value, Identities)
    if type(Value) is float:
        return format(Value, ".14g")
    if isinstance(Value, list):
        return [
            NormalState(ItemValue, Identities)
            for ItemValue in CastValue(list[object], Value)
        ]
    if isinstance(Value, Mapping):
        Fields = CastValue(Mapping[str, object], Value)
        return {
            NameValue: NormalState(ItemValue, Identities, NameValue)
            for NameValue, ItemValue in Fields.items()
            if NameValue != "TypeCode"
        }
    return Value


def NormalText(Value: str, Identities: dict[str, str]) -> str:
    Quantity = KNumberUnit.fullmatch(Value)
    if Quantity:
        return format(float(Quantity[1]), ".14g") + " " + Quantity[2]

    def ReplaceUuid(MatchValue: Match[str]) -> str:
        Identity = MatchValue[0].lower()
        if Identity not in Identities:
            Identities[Identity] = f"uuid:{len(Identities)}"
        return Identities[Identity]

    return KUuidPattern.sub(ReplaceUuid, Value)


def CompareNative(Source: DocumentModel, Expected: DocumentModel) -> None:
    if NormalState(NativeSummary(Source), {}) != NormalState(
        NativeSummary(Expected), {}
    ):
        raise ValueError(
            "Native Fusion state is outside the qualified authored feature profile"
        )
