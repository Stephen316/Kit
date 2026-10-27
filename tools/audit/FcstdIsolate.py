# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import json as JsonData
from pathlib import Path as FilePath
import subprocess as Subprocess
import sys as System

from tools.audit.FcstdContext import KRepositoryRoot
from tools.audit.FcstdResult import AuditRecord, MakeFailure, ReadAuditRecord

# bounded diagnostics keep failed workers useful without flooding recursive audit output
KErrorLimit = 1000

# worker timeout prevents malformed sources from blocking the remaining corpus indefinitely
KWorkerTimeout = 300


# worker invocation stays separate so timeout handling and result decoding remain focused
def RunProcess(
    SourcePath: FilePath, OutputRoot: FilePath, SourceIndex: int
) -> Subprocess.CompletedProcess[str]:
    return Subprocess.run(
        (
            System.executable,
            str(KRepositoryRoot / "tools" / "AuditFcstdSolidworks.py"),
            "--worker-source",
            str(SourcePath),
            "--worker-output",
            str(OutputRoot),
            "--worker-index",
            str(SourceIndex),
        ),
        cwd=KRepositoryRoot,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=KWorkerTimeout,
    )


# subprocess isolation lets recursive audits survive malformed or memory intensive sources
def AuditIsolated(
    SourcePath: FilePath,
    OutputRoot: FilePath,
    SourceIndex: int,
) -> AuditRecord:
    try:
        ProcessData = RunProcess(SourcePath, OutputRoot, SourceIndex)
    except Subprocess.TimeoutExpired as ErrorInfo:
        ErrorText = f"isolated worker timed out after {ErrorInfo.timeout} seconds"
        return MakeFailure(SourcePath, ErrorText)
    OutputLines = tuple(
        LineText.strip()
        for LineText in ProcessData.stdout.splitlines()
        if LineText.strip()
    )
    if ProcessData.returncode == 0 and OutputLines:
        try:
            ResultData: object = JsonData.loads(OutputLines[-1])
        except JsonData.JSONDecodeError:
            ResultData = None
        ParsedResult = ReadAuditRecord(ResultData)
        if ParsedResult is not None:
            return ParsedResult
    ErrorText = ProcessData.stderr.strip() or ProcessData.stdout.strip()
    if len(ErrorText) > KErrorLimit:
        ErrorText = ErrorText[-KErrorLimit:]
    FailureText = f"isolated worker exited {ProcessData.returncode}"
    if ErrorText:
        FailureText += f": {ErrorText}"
    return MakeFailure(SourcePath, FailureText)
