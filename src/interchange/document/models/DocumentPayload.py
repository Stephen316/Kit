# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import hashlib as HashCodec

from interchange.payloads.PayloadRoles import PayloadRole


# source recovery needs unambiguous document and digest binding payload indexes
def GetPayloadIds(DocumentValue: CadDocument) -> frozenset[int]:
    try:
        SourceDigest = bytes.fromhex(DocumentValue.source.sha256)
    except ValueError:
        return frozenset()
    if len(SourceDigest) != HashCodec.sha256().digest_size:
        return frozenset()
    SourceDigestText = DocumentValue.source.sha256.casefold()
    DocumentIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.brep_payloads)
        if PayloadValue.role == PayloadRole.KDocument
        and (
            HashCodec.sha256(PayloadValue.data).hexdigest()
            if PayloadValue.data is not None
            else PayloadValue.sha256.casefold()
        )
        == SourceDigestText
    )
    BindingIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.brep_payloads)
        if PayloadValue.role in (PayloadRole.KVerification, PayloadRole.KDocument)
        and PayloadValue.data == SourceDigest
        and PayloadValue.sha256.casefold() == HashCodec.sha256(SourceDigest).hexdigest()
    )
    if len(DocumentIndexes) != 1 or len(BindingIndexes) != 1:
        return frozenset()
    return frozenset((*DocumentIndexes, *BindingIndexes))


from interchange.document.models.DocumentModel import CadDocument  # noqa: E402
