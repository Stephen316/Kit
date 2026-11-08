# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
def HasKnownMetadata(Native: NativeParam) -> bool:
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
    Span: RecordSpan,
    Native: NativeParam,
    Actual: Parameter,
    BoundRank: int,
) -> NumberProofRow:
    if BulkData[Span.PayloadOffset : Span.PayloadOffset + 4] != bytes(
        4
    ) or not HasKnownMetadata(Native):
        raise ValueError("Fusion numeric record version or metadata remains unverified")
    Raw = ProjectParam(Native, Span)
    Owner = ResolveOwner(BulkData, Owners, Native, Span)
    Binding = None
    if Owner is not None:
        from convert.formats.Fusion.SourceProof.Bindings.ReadBindingProof import (
            ReadBindingProof,
        )

        Binding = ReadBindingProof(
            BulkData, Owners, Document, Native, Span, Actual, BoundRank
        )
        Raw = Replace(AttachOwner(Raw, *Owner), owner_id=Actual.owner_id)
    Expression = Actual.expression
    if (
        Replace(
            Actual,
            expression=(
                None if Expression is None else Replace(Expression, parameter_ids=())
            ),
        )
        != Raw
    ):
        raise ValueError("Fusion numeric record does not match its projected fields")
    return NumberProofRow(Span, Raw, Actual, Binding)


# native collection order determines independent global ordinals and bound binding ranks
def ReadNumberProofRows(
    Document: CadDocument,
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Order: tuple[int, ...],
    Names: dict[int, str],
) -> tuple[NumberProofRow, ...]:
    ById = {Param.id: Param for Param in Document.parameters}
    if (
        len(ById) != len(Document.parameters)
        or set(Order)
        != {
            Value.ObjectId for Value in Owners.values() if Value.ClassGuid == KParamGuid
        }
        or ById.keys() != {f"fusion-parameter-{Identity}" for Identity in Order}
    ):
        raise ValueError("Fusion numeric scope does not account for all parameters")
    Rank = 0
    Result = []
    for Index, Identity in enumerate(Order, start=1):
        Span = Owners[Identity]
        Native = ReadNativeNum(BulkData[Span.PayloadOffset + 4 : Span.EndOffset])
        Actual = ById[f"fusion-parameter-{Identity}"]
        if (
            Native.NativeIndex != Index
            or Native.ParamName != Names[Identity]
            or Actual.name != Native.ParamName
            or Actual.attributes.get("fusion.parameter_index") != Index
        ):
            raise ValueError(
                "Fusion numeric collection order disagrees with its parameters"
            )
        Rank += Native.BindingId is not None
        try:
            Result.append(
                ReadNumberRow(BulkData, Owners, Document, Span, Native, Actual, Rank)
            )
        except ValueError:
            continue
    return tuple(Result)
