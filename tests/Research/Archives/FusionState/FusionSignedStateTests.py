# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# a pinned process report guards complete journal transport and public refusals together
def CheckPrismState() -> None:
    RepoPath = FilePath(__file__).resolve().parents[4]
    Result = RunProcess(
        [PythonExe, "-B", "re/automation/FusionSignedPrism/VerifyJournalState.py"],
        cwd=RepoPath,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode(errors="replace")
    ActualDigest = DigestBytes(Result.stdout.replace(b"\r\n", b"\n")).hexdigest()
    assert (
        ActualDigest
        == "9cb493ca2f27ba479a0b8bd4dd13d88a54d643535e693e847a6e4259330c6f29"
    )
