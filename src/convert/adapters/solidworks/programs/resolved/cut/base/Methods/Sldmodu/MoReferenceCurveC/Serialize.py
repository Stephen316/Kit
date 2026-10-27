# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoReferenceCurveC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8032, 4, 3909, "primitive:ulong", 6),
            (8036, 4, 3928, "primitive:long", -1),
            (8040, 4, 3941, "primitive:long", 0),
            (8044, 4, 3954, "primitive:long", 0),
            (8048, 4, 3967, "primitive:ulong", 5),
            (8052, 4, 3986, "primitive:ulong", 5),
            (8060, 2, 4030, "primitive:ushort", 0),
            (8062, 4, 4154, "primitive:ulong", 4294967295),
            (8066, 4, 4250, "primitive:ulong", 0),
            (8074, 4, 4466, "primitive:long", 0),
            (8078, 4, 4482, "primitive:long", 0),
            (8082, 4, 4540, "primitive:long", 0),
            (13295, 4, 3909, "primitive:ulong", 6),
            (13299, 4, 3928, "primitive:long", -1),
            (13303, 4, 3941, "primitive:long", 0),
            (13307, 4, 3954, "primitive:long", 0),
            (13311, 4, 3967, "primitive:ulong", 5),
            (13315, 4, 3986, "primitive:ulong", 5),
            (13323, 2, 4030, "primitive:ushort", 0),
            (13325, 4, 4154, "primitive:ulong", 4294967295),
            (13329, 4, 4250, "primitive:ulong", 0),
            (13337, 4, 4466, "primitive:long", 0),
            (13341, 4, 4482, "primitive:long", 0),
            (13345, 4, 4540, "primitive:long", 0),
        ),
    },
)
