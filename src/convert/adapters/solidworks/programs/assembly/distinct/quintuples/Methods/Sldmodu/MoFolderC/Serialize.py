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
            (23760, 4, 155, "primitive:long", 1),
            (23764, 4, 210, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (195, 4, 155, "primitive:long", 0),
            (199, 4, 210, "primitive:long", 0),
            (394, 4, 155, "primitive:long", 1),
            (398, 4, 210, "primitive:long", 0),
            (596, 4, 155, "primitive:long", 1),
            (600, 4, 210, "primitive:long", 0),
            (1184, 4, 155, "primitive:long", 1),
            (1188, 4, 210, "primitive:long", 0),
            (1383, 4, 155, "primitive:long", 1),
            (1387, 4, 210, "primitive:long", 0),
            (1605, 4, 155, "primitive:long", 1),
            (1609, 4, 210, "primitive:long", 0),
            (1613, 4, 376, "primitive:long", 1),
            (1812, 4, 155, "primitive:long", 1),
            (1816, 4, 210, "primitive:long", 0),
            (2086, 4, 155, "primitive:long", 1),
            (2090, 4, 210, "primitive:long", 0),
            (2281, 4, 155, "primitive:long", 1),
            (2285, 4, 210, "primitive:long", 0),
            (2662, 4, 155, "primitive:long", 1),
            (2666, 4, 210, "primitive:long", 0),
            (2856, 4, 155, "primitive:long", 1),
            (2860, 4, 210, "primitive:long", 0),
        ),
    },
)
