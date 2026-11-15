import json as JsonCodec
import subprocess as Subprocess
import time as TimeClock
from pathlib import Path as FilePath


class DispatchWait:
    def __init__(self, Endpoint: FilePath) -> None:
        super().__init__()
        self.Endpoint = Endpoint

    def WaitFile(self, RelativePath: str) -> FilePath:
        TargetPath = self.Endpoint / RelativePath
        Until = TimeClock.monotonic() + 30
        while TimeClock.monotonic() < Until:
            if TargetPath.is_file():
                return TargetPath
            TimeClock.sleep(0.02)
        raise AssertionError(f"application file did not appear: {RelativePath}")

    def WaitRequest(self, Client: Subprocess.Popen[str]) -> FilePath:
        Until = TimeClock.monotonic() + 30
        while TimeClock.monotonic() < Until:
            Requests = sorted(self.Endpoint.glob("jobs/*/*.request"))
            if Requests:
                return Requests[0]
            if Client.poll() is not None:
                raise AssertionError(
                    f"application client exited before publishing: {Client.communicate(timeout=1)}"[
                        -4096:
                    ]
                )
            TimeClock.sleep(0.02)
        raise AssertionError("application client did not publish a request")

    def WaitHost(self, ProcessId: int) -> None:
        Until = TimeClock.monotonic() + 30
        while TimeClock.monotonic() < Until:
            ReadyFile = self.Endpoint / "ready.json"
            if (
                ReadyFile.is_file()
                and JsonCodec.loads(ReadyFile.read_text(encoding="utf-8"))["host"][
                    "pid"
                ]
                == ProcessId
            ):
                return
            TimeClock.sleep(0.02)
        raise AssertionError("new application counterpart did not register its process")
