import fcntl as FileLocks
import json as JsonCodec
import os as OsLayer
import secrets as Secrets
from collections.abc import Generator
from contextlib import contextmanager as ContextManager
from dataclasses import asdict as AsDictionary
from pathlib import Path as FilePath

from tests.Research.JobEntry import JobEntry
from tests.Research.JobLifecycle import JobLifecycle
from tests.Research.StoreState import StoreState


class MiniState(JobLifecycle):
    def __init__(self, Options: dict[str, object]) -> None:
        super().__init__()
        self.RootPath = FilePath(str(Options["root"])).resolve()
        (self.RootPath / "objects").mkdir(parents=True, exist_ok=True, mode=0o700)

    def LockPath(self) -> FilePath:
        return self.RootPath / "supervisor.lock"

    @ContextManager
    def OpenState(self) -> Generator[StoreState]:
        Handle = OsLayer.open(
            self.RootPath / "state.lock", OsLayer.O_CREAT | OsLayer.O_RDWR, 0o600
        )
        try:
            FileLocks.flock(Handle, FileLocks.LOCK_EX)
            StatePath = self.RootPath / "state.json"
            if StatePath.is_file():
                RawState = JsonCodec.loads(StatePath.read_text(encoding="utf-8"))
                Current = StoreState(
                    JobMap={
                        ItemName: JobEntry(**Entry)
                        for ItemName, Entry in RawState["JobMap"].items()
                    },
                    Bindings=RawState["Bindings"],
                    Pools=RawState["Pools"],
                    Capacity=RawState["Capacity"],
                    Counter=RawState["Counter"],
                )
            else:
                Current = StoreState({}, {}, {}, {}, 0)
            self.SettleJobsMut(Current)
            yield Current
            self.SettleJobsMut(Current)
            StagePath = self.RootPath / f".state-{Secrets.token_hex(8)}"
            _ = StagePath.write_text(
                JsonCodec.dumps(AsDictionary(Current)), encoding="utf-8"
            )
            OsLayer.replace(StagePath, StatePath)
        finally:
            OsLayer.close(Handle)
