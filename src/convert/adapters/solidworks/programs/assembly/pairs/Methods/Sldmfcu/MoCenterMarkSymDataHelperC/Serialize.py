# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoCenterMarkSymDataHelperC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (18566, 1, 297, "primitive:uchar", 0),
            (18567, 8, 317, "primitive:double", float.fromhex("0x0.0p+0")),
            (18575, 1, 330, "primitive:uchar", 1),
            (18576, 8, 350, "primitive:double", float.fromhex("0x0.0p+0")),
            (18584, 1, 363, "primitive:uchar", 0),
            (18585, 1, 383, "primitive:uchar", 0),
            (18586, 1, 403, "primitive:uchar", 0),
            (18587, 1, 423, "primitive:uchar", 0),
            (18588, 1, 443, "primitive:uchar", 0),
            (18589, 1, 463, "primitive:uchar", 0),
            (18729, 4, 534, "primitive:int", 0),
            (18733, 1, 563, "primitive:uchar", 1),
            (18734, 1, 583, "primitive:uchar", 1),
            (18735, 1, 603, "primitive:uchar", 1),
            (18736, 1, 639, "primitive:uchar", 0),
            (18737, 8, 675, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
