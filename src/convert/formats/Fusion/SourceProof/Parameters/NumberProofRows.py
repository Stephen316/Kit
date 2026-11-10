# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.ParamBinding import ResolveOwner
from convert.formats.Fusion.ParamProjection import AttachOwner, ProjectParam
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Parameters.NumberProofRow import NumberProofRow
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordParameter import Parameter


# only observed metadata dialects account for the numeric record flags and favorite bit
def HasKnownMeta(Native: NativeParam) -> bool:
    Metadata = Native.Metadata
    IsUser = Native.BindingId is None
    return (
        len(Metadata) == 10
        and Metadata[:7] == bytes(7)
        and Metadata[7] in (0, 1)
        and Metadata[8:] == bytes((0, IsUser))
    ) or (not IsUser and Metadata == bytes(11))


# owner copies and feature controls must corroborate a bound parameter before it can be trusted
def ReadNumberRow(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    SpanValue: RecordSpan,
    Native: NativeParam,
    Actual: Parameter,
    BoundRank: int,
) -> NumberProofRow:
    if BulkData[SpanValue.PayloadOffset : SpanValue.PayloadOffset + 4] != bytes(
        4
    ) or not HasKnownMeta(Native):
        raise ValueError("Fusion numeric record version or metadata remains unverified")
    RawValue = ProjectParam(Native, SpanValue)
    Owner = ResolveOwner(BulkData, Owners, Native, SpanValue)
    Binding = None
    if Owner is not None:
        from convert.formats.Fusion.SourceProof.Bindings.ReadBindingProof import (
            ReadBindProof,
        )

        Binding = ReadBindProof(
            BulkData, Owners, Document, Native, SpanValue, Actual, BoundRank
        )
        RawValue = Replace(AttachOwner(RawValue, *Owner), owner_id=Actual.owner_id)
    Expression = Actual.expression
    if (
        Replace(
            Actual,
            expression=(
                None if Expression is None else Replace(Expression, parameter_ids=())
            ),
        )
        != RawValue
    ):
        raise ValueError("Fusion numeric record does not match its projected fields")
    return NumberProofRow(SpanValue, RawValue, Actual, Binding)


# native collection order determines independent global ordinals and bound binding ranks
def ReadNumberRows(
    Document: CadDocument,
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Order: tuple[int, ...],
    Names: dict[int, str],
) -> tuple[NumberProofRow, ...]:
    ByIdentity = {Param.id: Param for Param in Document.parameters}
    if (
        len(ByIdentity) != len(Document.parameters)
        or set(Order)
        != {
            Value.ObjectId for Value in Owners.values() if Value.ClassGuid == KParamGuid
        }
        or ByIdentity.keys() != {f"fusion-parameter-{Identity}" for Identity in Order}
    ):
        raise ValueError("Fusion numeric scope does not account for all parameters")
    RankValue = 0
    Result: list[NumberProofRow] = []
    for Index, Identity in enumerate(Order, start=1):
        SpanValue = Owners[Identity]
        Native = ReadNativeNum(
            BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset]
        )
        Actual = ByIdentity[f"fusion-parameter-{Identity}"]
        if (
            Native.NativeIndex != Index
            or Native.ParamName != Names[Identity]
            or Actual.name != Native.ParamName
            or Actual.attributes.get("fusion.parameter_index") != Index
        ):
            raise ValueError(
                "Fusion numeric collection order disagrees with its parameters"
            )
        RankValue += Native.BindingId is not None
        try:
            Result.append(
                ReadNumberRow(
                    BulkData, Owners, Document, SpanValue, Native, Actual, RankValue
                )
            )
        except ValueError:
            continue
    return tuple(Result)
