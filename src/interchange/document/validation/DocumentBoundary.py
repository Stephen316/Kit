# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.document.models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)


# nested records can be malformed at runtime so validators narrow them before use
def GetDocument(SourceValue: object) -> CadDocument | None:
    return SourceValue if isinstance(SourceValue, CadDocument) else None
