# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.FormulaDeps.ScopedParams import ReadPartScope
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Parameters.NumberProofFormulas import (
    ReadProvenNumbers,
)
from convert.formats.Fusion.SourceProof.Parameters.NumberProofRows import (
    ReadNumberProofRows,
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
            BulkData[Span.PayloadOffset : Span.PayloadOffset + 4] != bytes(4)
            for Span in (Collection, Registry)
        ):
            return ()
        Rows = ReadNumberProofRows(Document, BulkData, Owners, Order, Names)
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
    for Row in ReadProvenNumbers(Rows):
        Claims.append(
            ProofClaim(
                Scope,
                Row.Span,
                ProofCategory.KVerifiedDesign,
                "scoped numeric parameter and formula",
            )
        )
        if Row.Binding is not None:
            Claims.append(
                ProofClaim(
                    Scope,
                    Row.Binding,
                    ProofCategory.KVerifiedDesign,
                    "reciprocal typed parameter binding",
                )
            )
    return tuple(Claims)
