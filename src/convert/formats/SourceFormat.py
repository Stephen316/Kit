# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import CadDocument

from convert.adapters import CadReaderAdapter as ReaderAdapter


# source aliases survive conversion because readers may report a canonical family format
def ResolveFormat(DocumentData: CadDocument, ReaderData: ReaderAdapter) -> str:
    SourceIds = {
        ValueText.casefold()
        for ValueText in (ReaderData.info.format_id, *ReaderData.info.aliases)
    }
    if DocumentData.source.format_id.casefold() in SourceIds:
        return DocumentData.source.format_id
    return ReaderData.info.format_id
