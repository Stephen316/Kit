import json as JsonCodec
import subprocess as Subprocess
import time as TimeClock
from pathlib import Path as FilePath


# transport checks share readiness barriers because process startup order is nondeterministic
class DispatchWait:

    # readiness observations must stay bound to the same private endpoint as the application host
    def __init__(self, Endpoint: FilePath) -> None:
        super().__init__()
        self.Endpoint = Endpoint

    # callers need file publication evidence before treating an asynchronous transport phase as reached
    def WaitFile(self, RelativePath: str) -> FilePath:
        TargetPath = self.Endpoint / RelativePath
        Until = TimeClock.monotonic() + 30
        while TimeClock.monotonic() < Until:
            if TargetPath.is_file():
                return TargetPath
            TimeClock.sleep(0.02)
        raise AssertionError(f"application file did not appear: {RelativePath}")

    # request checks must distinguish unpublished work from a client that already exited
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

    # readiness from an old host cannot establish that its replacement has acquired the endpoint
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
