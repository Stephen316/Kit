# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoThreedViewC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (230, 4, 3488, "primitive:long", 0),
            (238, 4, 3856, "primitive:long", 0),
            (242, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (252, 4, 4072, "primitive:long", 0),
            (256, 4, 4088, "primitive:long", 1),
            (262, 4, 4241, "primitive:long", -1),
            (266, 4, 4316, "primitive:long", 0),
            (270, 4, 4389, "primitive:long", -1),
            (274, 4, 4444, "primitive:long", -1),
            (488, 4, 3488, "primitive:long", 0),
            (496, 4, 3856, "primitive:long", 0),
            (500, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (510, 4, 4072, "primitive:long", 0),
            (514, 4, 4088, "primitive:long", 1),
            (520, 4, 4241, "primitive:long", -1),
            (524, 4, 4316, "primitive:long", 0),
            (528, 4, 4389, "primitive:long", -1),
            (532, 4, 4444, "primitive:long", -1),
        ),
    },
)
