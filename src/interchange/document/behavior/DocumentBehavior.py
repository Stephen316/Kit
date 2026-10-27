# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.document.behavior.DocumentIoBehavior import DocumentIo
from interchange.document.behavior.DocumentLookupBehavior import DocumentLookup
from interchange.document.behavior.DocumentValidBehavior import DocumentValid


# focused method contracts keep the immutable document schema independently reviewable
class DocumentApi(DocumentIo, DocumentValid, DocumentLookup):
    KSlotsValue = ()

    locals()["__slots__"] = KSlotsValue
