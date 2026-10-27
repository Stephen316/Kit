# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldasmu.UiAssemblyDocC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Definition": (
            (3802, 4, 378, "primitive:long", 0),
            (3806, 4, 451, "primitive:long", 0),
            (3818, 4, 654, "primitive:long", 0),
            (3822, 4, 734, "primitive:long", 0),
            (3826, 8, 750, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (3834, 4, 817, "primitive:long", 0),
            (3890, 4, 944, "primitive:long", 10),
        ),
    },
)
