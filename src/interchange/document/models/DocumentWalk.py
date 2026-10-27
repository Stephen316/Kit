# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Iterator as ValueIterator


# nested assembly documents need cycle safe traversal for aggregate operations
def WalkDocuments(DocumentValue: CadDocument) -> ValueIterator[CadDocument]:
    from interchange.document.validation.DocumentBoundary import GetDocument

    PendingValues = [DocumentValue]
    SeenValues: set[int] = set()
    while PendingValues:
        ItemValue = PendingValues.pop()
        IdentityValue = id(ItemValue)
        if IdentityValue in SeenValues:
            continue
        SeenValues.add(IdentityValue)
        yield ItemValue
        if ItemValue.assembly is None:
            continue
        for ComponentValue in reversed(ItemValue.assembly.documents):
            NestedValue = GetDocument(ComponentValue.document)
            if NestedValue is not None:
                PendingValues.append(NestedValue)


from interchange.document.models.DocumentModel import CadDocument  # noqa: E402
