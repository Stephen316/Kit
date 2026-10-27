# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import json as JsonData


# json quoting provides valid yaml scalars without maintaining duplicate escaping rules
def QuoteYaml(ValueText: str) -> str:
    return JsonData.dumps(ValueText, ensure_ascii=False)
