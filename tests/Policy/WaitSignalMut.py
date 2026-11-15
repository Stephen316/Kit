from __future__ import annotations as Annotations

from queue import Empty as EmptyQueue, Queue as QueueInfo
from time import monotonic as ReadClock


# the expected wait message distinguishes startup latency from aggregate readiness defects
def WaitSignalMut(LineQueue: QueueInfo[bytes], PendingCheck: str) -> None:
    ExpectedText = f"Waiting for {PendingCheck}".encode()
    OutputData = bytearray()
    Deadline = ReadClock() + 30.0
    while ExpectedText not in OutputData:
        RemainSecs = Deadline - ReadClock()
        FailureText = f"CI aggregate never waited for {PendingCheck}\n"
        if RemainSecs <= 0:
            raise AssertionError(FailureText + OutputData.decode(errors="replace"))
        try:
            LineInfo = LineQueue.get(timeout=RemainSecs)
        except EmptyQueue as ErrorInfo:
            FailureText += OutputData.decode(errors="replace")
            raise AssertionError(FailureText) from ErrorInfo
        FailureText = f"CI aggregate stopped before waiting for {PendingCheck}\n"
        assert LineInfo, FailureText + OutputData.decode(errors="replace")
        OutputData.extend(LineInfo)
