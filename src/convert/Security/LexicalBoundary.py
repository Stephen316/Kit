# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from os import PathLike as PathLikeValue
from os.path import abspath as AbsolutePath
from pathlib import Path as PathInfo


# lexical containment blocks traversal before candidate paths reach filesystem operations
def ResolveLexical(PathValue: str | PathLikeValue[str], RootPath: PathInfo) -> PathInfo:
    CandidatePath = PathInfo(PathValue)
    if not CandidatePath.is_absolute():
        CandidatePath = RootPath / CandidatePath
    LexicalPath = PathInfo(AbsolutePath(CandidatePath))
    _ = LexicalPath.relative_to(RootPath)
    return LexicalPath
