# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# the manual witness must refuse changed receipts processes controls and restored bytes
def CheckWitness(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Program = (
        RootPath
        / "re/Fusion/Reconstruction/DimensionAuthoring/WitnessBoundaryFixture.py"
    )
    Process = Subprocess.run(
        [System.executable, "-B", str(Program), str(TmpPath)],
        cwd=RootPath,
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )
    assert Process.returncode == 0, Process.stderr
    assert JsonCodec.loads(Process.stdout) == {
        "verified_synthetic_contract": True,
        "rejected_mutations": 4,
    }
