from __future__ import annotations as Annotations

from subprocess import Popen as OpenProcess
from threading import Thread as ReaderThread


# owned children and readers must finish before their probe workspace disappears
def ReleaseChildMut(ProcessInfo: OpenProcess[bytes], ReaderInfo: ReaderThread) -> None:
    if ProcessInfo.poll() is None:
        ProcessInfo.kill()
    _ = ProcessInfo.wait(timeout=5.0)
    ReaderInfo.join(timeout=5.0)
    assert not ReaderInfo.is_alive()
