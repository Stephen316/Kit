# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9115, 4, 7121, "primitive:long", 1),
            (9143, 8, 7292, "primitive:double", float.fromhex("0x1.bbe1e7e52c384p-5")),
            (14439, 4, 7121, "primitive:long", 1),
            (14467, 8, 7292, "primitive:double", float.fromhex("0x1.bbe1e7e52c384p-5")),
        ),
    },
)
