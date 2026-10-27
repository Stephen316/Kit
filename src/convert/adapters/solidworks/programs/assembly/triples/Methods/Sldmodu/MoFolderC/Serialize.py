# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFolderC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (23156, 4, 155, "primitive:long", 1),
            (23160, 4, 210, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (1072, 4, 155, "primitive:long", 1),
            (1076, 4, 210, "primitive:long", 0),
            (1271, 4, 155, "primitive:long", 1),
            (1275, 4, 210, "primitive:long", 0),
            (1493, 4, 155, "primitive:long", 1),
            (1497, 4, 210, "primitive:long", 0),
            (1501, 4, 376, "primitive:long", 1),
            (1700, 4, 155, "primitive:long", 1),
            (1704, 4, 210, "primitive:long", 0),
            (1974, 4, 155, "primitive:long", 1),
            (1978, 4, 210, "primitive:long", 0),
            (2169, 4, 155, "primitive:long", 1),
            (2173, 4, 210, "primitive:long", 0),
            (2550, 4, 155, "primitive:long", 1),
            (2554, 4, 210, "primitive:long", 0),
            (2744, 4, 155, "primitive:long", 1),
            (2748, 4, 210, "primitive:long", 0),
        ),
    },
)
