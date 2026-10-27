# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import re as Regex

from tools.Policy.PolicyRules import KStemPattern


# one predicate keeps filename enforcement identical across full and changed scans
def IsValidStem(StemText: str) -> bool:
    return Regex.fullmatch(KStemPattern, StemText) is not None
