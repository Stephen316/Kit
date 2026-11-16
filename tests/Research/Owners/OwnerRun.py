import json as JsonCodec
from types import TracebackType
from typing import Self

from tests.Research.Owners.KillOwner import KillOwner
from tests.Research.SupervisorClient import SessionHost


# ownership scenarios require scoped teardown even when an intermediate process assertion fails
class OwnerRun:

    # restart tests need a known supervisor and gate location before waiting on ownership evidence
    def __init__(self, Harness: SessionHost, IdleSeconds: int = 30) -> None:
        super().__init__()
        self.GateRoot = Harness.RootPath / "Gate"
        self.Process = Harness.StartRun(
            "--idle-seconds", str(IdleSeconds), "--max-seconds", "60"
        )
        self.ProcessId: int | None = None

    # callers need the scoped fixture while cleanup remains attached to the process lifetime
    def __enter__(self) -> Self:
        return self

    # failed assertions must release the barrier and retire only the process tree the fixture owns
    def __exit__(
        self,
        ErrorKind: type[BaseException] | None,
        ErrorValue: BaseException | None,
        TraceInfo: TracebackType | None,
    ) -> None:
        if self.Process.poll() is None:
            if self.ProcessId is None:
                for RecordFile in (self.GateRoot / "Processes").glob("*.json"):
                    Record = JsonCodec.loads(RecordFile.read_text(encoding="utf-8"))
                    if (
                        Record["pid"] == self.Process.pid
                        or Record["parent_pid"] == self.Process.pid
                    ):
                        self.ProcessId = int(Record["pid"])
            if self.ProcessId is not None:
                KillOwner(self.ProcessId, Required=False)
            if self.Process.poll() is None:
                self.Process.kill()
        _ = self.Process.communicate(timeout=15)
