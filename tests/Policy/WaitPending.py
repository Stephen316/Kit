from __future__ import annotations as Annotations

from collections.abc import Mapping
from pathlib import Path as FilePath
from queue import Queue as QueueInfo
from subprocess import (
    PIPE as KStdoutPipe,
    STDOUT as KMergeErrors,
    Popen as OpenProcess,
    TimeoutExpired as WaitExpired,
)
from threading import Thread as ReaderThread

from pytest import raises as RaisesError

from tests.Policy.ReadLinesMut import ReadLinesMut
from tests.Policy.ReleaseChildMut import ReleaseChildMut
from tests.Policy.WaitSignalMut import WaitSignalMut


# command probes need observable pending state before asserting continued liveness
def WaitPending(
    ArgList: list[str],
    WorkPath: FilePath,
    EnvValues: Mapping[str, str],
    PendingCheck: str,
) -> None:
    with OpenProcess(
        ArgList,
        cwd=WorkPath,
        env=EnvValues,
        stdout=KStdoutPipe,
        stderr=KMergeErrors,
    ) as ProcessInfo:
        StdoutInfo = ProcessInfo.stdout
        assert StdoutInfo is not None
        LineQueue = QueueInfo[bytes]()
        ReaderInfo = ReaderThread(
            target=ReadLinesMut, args=(StdoutInfo, LineQueue), daemon=True
        )
        ReaderInfo.start()
        try:
            WaitSignalMut(LineQueue, PendingCheck)
            with RaisesError(WaitExpired):
                _ = ProcessInfo.wait(timeout=2.0)
        finally:
            ReleaseChildMut(ProcessInfo, ReaderInfo)
