# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

# kiro specific metadata stays explicit because agent skills frontmatter cannot infer source inclusion
KSkillMetadata = {
    "workos-token-verification": {
        "kiro-inclusion": "fileMatch",
        "kiro-file-match-pattern": "backend/**/*.py",
    }
}
