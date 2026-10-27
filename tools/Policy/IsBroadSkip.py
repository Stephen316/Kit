# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations


# example cad inputs preserve external identities so only that subtree bypasses every rule
def IsBroadSkip(RepoPath: str) -> bool:
    return RepoPath.startswith("examples/")
