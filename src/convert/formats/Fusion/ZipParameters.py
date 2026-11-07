# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable

from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.ParamBinding import ResolveOwner
from convert.formats.Fusion.ParamProjection import (
    AttachOwner,
    ParamOrigin,
    ProjectParam,
)
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# preserve unsupported registered parameter records as explicit diagnostics
def ReadZipParams(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> tuple[tuple[Parameter, ...], tuple[Diagnostic, ...]]:
    BulkData, Spans = ReadDesignZip(DataValue, InflateZstd)
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Parameters: list[Parameter] = []
    Diagnostics: list[Diagnostic] = []
    for SpanValue in Spans:
        if not SpanValue.IsPrimary or SpanValue.ClassGuid != KParamGuid:
            continue
        try:
            BodyValue = BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset]
            ParamData = ReadNativeNum(BodyValue)
            ParamValue = ProjectParam(ParamData, SpanValue)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.parameter.unsupported",
                    message=str(ErrorInfo),
                    provenance=ParamOrigin(SpanValue),
                )
            )
            continue
        try:
            Owner = ResolveOwner(BulkData, Owners, ParamData, SpanValue)
            if Owner is not None:
                ParamValue = AttachOwner(ParamValue, *Owner)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.parameter.binding",
                    message=str(ErrorInfo),
                    provenance=ParamOrigin(SpanValue),
                )
            )
        Parameters.append(ParamValue)
    return tuple(Parameters), tuple(Diagnostics)
