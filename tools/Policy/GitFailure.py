# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations


# repository access failures need a dedicated boundary so policy violations remain distinguishable
class GitFailure(RuntimeError):

    # callers need useful git context without depending on subprocess implementation details
    def __init__(self, MessageText: str) -> None:
        super().__init__(MessageText)
