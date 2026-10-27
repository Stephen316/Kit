# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import argparse as Argparse
import json as JsonData


# worker mode isolates risky documents while retaining one public command entry point
def RunWorker(ArgumentsData: Argparse.Namespace) -> int:
    from tools.audit.FcstdAudit import AuditSource

    WorkerSource = ArgumentsData.worker_source
    WorkerOutput = ArgumentsData.worker_output
    WorkerIndex = ArgumentsData.worker_index
    if WorkerOutput is None or WorkerIndex is None:
        raise SystemExit("audit worker arguments are incomplete")
    ResultData = AuditSource(
        WorkerSource.resolve(),
        WorkerOutput.resolve(),
        WorkerIndex,
    )
    print(JsonData.dumps(ResultData, separators=(",", ":")))
    return 0
