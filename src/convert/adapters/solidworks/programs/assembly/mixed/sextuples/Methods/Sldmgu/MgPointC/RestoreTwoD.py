# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgPointC.RestoreTwoD import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4894, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (4902, 8, 54, "primitive:double", float.fromhex("0x0.0p+0")),
            (4924, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (4932, 8, 54, "primitive:double", float.fromhex("0x0.0p+0")),
            (4940, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (4948, 8, 54, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
