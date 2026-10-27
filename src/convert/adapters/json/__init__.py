# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.json.Adapter import JsonAdapter

# package exports stay explicit so static analysis recognizes the public adapter
__all__ = ("JsonAdapter",)
