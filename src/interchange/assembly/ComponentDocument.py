# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.document.models.DocumentModel import (
    ComponentDoc,
)

# historical import paths stay importable because pickles and adapters resolve component records here
__all__ = ("ComponentDoc",)
