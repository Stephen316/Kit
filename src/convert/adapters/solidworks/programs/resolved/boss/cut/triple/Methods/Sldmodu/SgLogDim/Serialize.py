# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (6079, 2, 239, "primitive:ushort", 65534),
            (6081, 2, 334, "primitive:ushort", 0),
            (7978, 2, 239, "primitive:ushort", 65534),
            (7980, 2, 334, "primitive:ushort", 0),
            (8033, 2, 239, "primitive:ushort", 65534),
            (8035, 2, 334, "primitive:ushort", 0),
            (8088, 2, 239, "primitive:ushort", 65534),
            (8090, 2, 334, "primitive:ushort", 0),
            (8143, 2, 239, "primitive:ushort", 65534),
            (8145, 2, 334, "primitive:ushort", 0),
            (13173, 2, 239, "primitive:ushort", 65534),
            (13175, 2, 334, "primitive:ushort", 0),
            (13228, 2, 239, "primitive:ushort", 65534),
            (13230, 2, 334, "primitive:ushort", 0),
            (13283, 2, 239, "primitive:ushort", 65534),
            (13285, 2, 334, "primitive:ushort", 0),
            (13338, 2, 239, "primitive:ushort", 65534),
            (13340, 2, 334, "primitive:ushort", 0),
            (18334, 2, 239, "primitive:ushort", 65534),
            (18336, 2, 334, "primitive:ushort", 0),
            (18389, 2, 239, "primitive:ushort", 65534),
            (18391, 2, 334, "primitive:ushort", 0),
            (18444, 2, 239, "primitive:ushort", 65534),
            (18446, 2, 334, "primitive:ushort", 0),
            (18499, 2, 239, "primitive:ushort", 65534),
            (18501, 2, 334, "primitive:ushort", 0),
            (23404, 2, 239, "primitive:ushort", 65534),
            (23406, 2, 334, "primitive:ushort", 0),
            (23459, 2, 239, "primitive:ushort", 65534),
            (23461, 2, 334, "primitive:ushort", 0),
            (23514, 2, 239, "primitive:ushort", 65534),
            (23516, 2, 334, "primitive:ushort", 0),
            (23569, 2, 239, "primitive:ushort", 65534),
            (23571, 2, 334, "primitive:ushort", 0),
        ),
    },
)
