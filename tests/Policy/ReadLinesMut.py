from __future__ import annotations as Annotations

from queue import Queue as QueueInfo
from typing import IO as StreamIO


# draining output prevents child pipe pressure from changing pending behavior
def ReadLinesMut(StreamInfo: StreamIO[bytes], LineQueue: QueueInfo[bytes]) -> None:
    try:
        for LineInfo in StreamInfo:
            LineQueue.put(LineInfo)
    finally:
        LineQueue.put(b"")
