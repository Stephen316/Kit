# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgMatrixC.Restore import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (4260, 8, 90, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4268, 8, 103, "primitive:double", float.fromhex("0x0.0p+0")),
            (4276, 8, 116, "primitive:double", float.fromhex("0x0.0p+0")),
            (4284, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (4292, 8, 144, "primitive:double", float.fromhex("0x0.0p+0")),
            (4300, 8, 158, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4308, 8, 172, "primitive:double", float.fromhex("0x0.0p+0")),
            (4316, 8, 186, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (4324, 8, 200, "primitive:double", float.fromhex("0x0.0p+0")),
            (4830, 8, 90, "primitive:double", float.fromhex("-0x0.0p+0")),
            (4838, 8, 103, "primitive:double", float.fromhex("0x0.0p+0")),
            (4846, 8, 116, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4854, 8, 130, "primitive:double", float.fromhex("-0x0.0p+0")),
            (4862, 8, 144, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4870, 8, 158, "primitive:double", float.fromhex("0x0.0p+0")),
            (4878, 8, 172, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (4886, 8, 186, "primitive:double", float.fromhex("0x0.0p+0")),
            (4894, 8, 200, "primitive:double", float.fromhex("0x0.0p+0")),
            (10728, 8, 90, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10736, 8, 103, "primitive:double", float.fromhex("0x0.0p+0")),
            (10744, 8, 116, "primitive:double", float.fromhex("0x0.0p+0")),
            (10752, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (10760, 8, 144, "primitive:double", float.fromhex("0x0.0p+0")),
            (10768, 8, 158, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10776, 8, 172, "primitive:double", float.fromhex("0x0.0p+0")),
            (10784, 8, 186, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (10792, 8, 200, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
