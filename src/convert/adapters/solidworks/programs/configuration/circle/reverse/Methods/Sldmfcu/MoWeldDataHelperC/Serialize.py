# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoWeldDataHelperC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (16710, 1, 719, "primitive:uchar", 0),
            (16779, 1, 878, "primitive:uchar", 0),
            (16780, 1, 901, "primitive:uchar", 0),
            (16781, 1, 924, "primitive:uchar", 0),
            (16782, 1, 947, "primitive:uchar", 0),
            (16787, 1, 986, "primitive:uchar", 0),
            (16788, 1, 1009, "primitive:uchar", 0),
            (16789, 4, 1039, "primitive:long", 0),
            (16793, 4, 1058, "primitive:long", 0),
            (16797, 1, 1076, "primitive:uchar", 0),
            (16798, 1, 1096, "primitive:uchar", 0),
            (16799, 1, 1116, "primitive:uchar", 0),
            (16800, 4, 1039, "primitive:long", 0),
            (16804, 4, 1058, "primitive:long", 0),
            (16808, 1, 1076, "primitive:uchar", 0),
            (16809, 1, 1096, "primitive:uchar", 0),
            (16810, 1, 1116, "primitive:uchar", 0),
            (16811, 4, 1146, "primitive:long", 0),
            (16815, 1, 1168, "primitive:uchar", 0),
            (16816, 1, 1191, "primitive:uchar", 1),
            (16837, 1, 1251, "primitive:uchar", 0),
            (16838, 1, 1274, "primitive:uchar", 0),
            (16839, 1, 1297, "primitive:uchar", 0),
            (16840, 1, 1320, "primitive:uchar", 0),
            (16841, 1, 1343, "primitive:uchar", 0),
            (16842, 1, 1366, "primitive:uchar", 0),
            (16843, 1, 1389, "primitive:uchar", 0),
            (16932, 1, 1444, "primitive:uchar", 1),
            (17021, 1, 1499, "primitive:uchar", 1),
        ),
    },
)
