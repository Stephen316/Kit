# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.FormulaDeps.ScopedParams import ReadPartScope
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Parameters.NumberProofFormulas import (
    ReadProvenNums,
)
from convert.formats.Fusion.SourceProof.Parameters.NumberProofRows import (
    ReadNumberRows,
)
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)
from interchange.document.models.DocumentModel import CadDocument


# exact numeric evidence can settle only records whose scope and semantics are independently verified
def ReadParamClaims(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    Scope: ProofScope,
) -> tuple[ProofClaim, ...]:
    try:
        Owners, Collection, Registry, Order, Names = ReadPartScope(
            BulkData, Spans, History, VerifyOrder=True
        )
        if any(
            BulkData[SpanValue.PayloadOffset : SpanValue.PayloadOffset + 4] != bytes(4)
            for SpanValue in (Collection, Registry)
        ):
            return ()
        RowValues = ReadNumberRows(Document, BulkData, Owners, Order, Names)
    except ValueError:
        return ()
    Claims = [
        ProofClaim(
            Scope,
            Collection,
            ProofCategory.KVerifiedDesign,
            "ordered parameter collection",
        ),
        ProofClaim(
            Scope,
            Registry,
            ProofCategory.KObserved,
            "reciprocal parameter name registry",
        ),
    ]
    for RowValue in ReadProvenNums(RowValues):
        Claims.append(
            ProofClaim(
                Scope,
                RowValue.Span,
                ProofCategory.KVerifiedDesign,
                "scoped numeric parameter and formula",
            )
        )
        if RowValue.Binding is not None:
            Claims.append(
                ProofClaim(
                    Scope,
                    RowValue.Binding,
                    ProofCategory.KVerifiedDesign,
                    "reciprocal typed parameter binding",
                )
            )
    return tuple(Claims)
