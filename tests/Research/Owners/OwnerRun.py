import json as JsonCodec
from types import TracebackType
from typing import Self

from tests.Research.Owners.KillOwner import KillOwner
from tests.Research.SupervisorClient import SessionHost


class OwnerRun:
    def __init__(self, Harness: SessionHost) -> None:
        super().__init__()
        self.GateRoot = Harness.RootPath / "Gate"
        self.Process = Harness.StartRun("--idle-seconds", "30", "--max-seconds", "60")
        self.ProcessId: int | None = None

    def __enter__(self) -> Self:
        return self

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
