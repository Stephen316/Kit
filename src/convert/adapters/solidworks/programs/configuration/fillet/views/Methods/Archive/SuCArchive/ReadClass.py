# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Archive.SuCArchive.ReadClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (0, 24, "SuCArchiveReadClass", "definition", ("moAnnotationView_c", 1)),
            (234, 2, "SuCArchiveReadClass", "null", 0),
            (236, 2, "SuCArchiveReadClass", "null", 0),
            (250, 2, "SuCArchiveReadClass", "null", 0),
            (260, 2, "SuCArchiveReadClass", "null", 0),
            (278, 2, "SuCArchiveReadClass", "classref", 100),
            (492, 2, "SuCArchiveReadClass", "null", 0),
            (494, 2, "SuCArchiveReadClass", "null", 0),
            (508, 2, "SuCArchiveReadClass", "null", 0),
            (518, 2, "SuCArchiveReadClass", "null", 0),
            (552, 2, "SuCArchiveReadClass", "null", 0),
            (578, 2, "SuCArchiveReadClass", "null", 0),
        ),
    },
)
