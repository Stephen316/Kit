import hashlib as Hashing
import json as JsonCodec
import os as OsLayer
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


def GateCommand() -> int:
    GateRoot = FilePath(System.argv[1])
    OwnerPid = int(System.argv[2])
    HeldCommand = System.argv[3]
    Command = System.argv[5:]
    Index = Command.index("--store") + 2
    if Command[Index] == "--owner":
        Index += 2
    Operation = Command[Index]
    IsHeld = False
    if Operation == HeldCommand:
        try:
            Handle = OsLayer.open(
                GateRoot / "Held.json",
                OsLayer.O_CREAT | OsLayer.O_EXCL | OsLayer.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            pass
        else:
            Destination = Command[
                Command.index("--claim-file" if Operation == "claim" else "--claim-dir")
                + 1
            ]
            with OsLayer.fdopen(Handle, "w", encoding="utf-8") as Output:
                _ = Output.write(
                    JsonCodec.dumps(
                        {
                            "supervisor_pid": OwnerPid,
                            "gate_pid": OsLayer.getpid(),
                            "parent_pid": OsLayer.getppid(),
                            "destination": Destination,
                        }
                    )
                )
            IsHeld = True
            Until = TimeClock.monotonic() + 60
            while not (GateRoot / "Release").exists() and TimeClock.monotonic() < Until:
                TimeClock.sleep(0.02)
    Result = Subprocess.run(
        Command, capture_output=True, text=True, check=False, timeout=45
    )
    RecordResult(GateRoot, OwnerPid, Command, Operation, IsHeld, Result)
    _ = System.stdout.write(Result.stdout)
    _ = System.stderr.write(Result.stderr)
    return Result.returncode


def RecordResult(
    GateRoot: FilePath,
    OwnerPid: int,
    Command: list[str],
    Operation: str,
    IsHeld: bool,
    Result: Subprocess.CompletedProcess[str],
) -> None:
    if Operation == "rotate-owner" and Result.returncode == 0:
        Owner = Command[Command.index("--new-owner") + 1]
        Stage = GateRoot / f".Owner-{OwnerPid}.json"
        _ = Stage.write_text(
            JsonCodec.dumps(
                {
                    "pid": OwnerPid,
                    "digest": Hashing.sha256(Owner.encode("ascii")).hexdigest(),
                }
            ),
            encoding="utf-8",
        )
        OsLayer.replace(Stage, GateRoot / "Owner.json")
    if IsHeld:
        _ = (GateRoot / "Result.json").write_text(
            JsonCodec.dumps(
                {"exit_status": Result.returncode, "stderr": Result.stderr}
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    System.exit(GateCommand())
