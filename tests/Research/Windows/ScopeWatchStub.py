import json as JsonCodec
import os as OsLayer
import runpy as ScriptRun
import subprocess as Subprocess
import sys as System
import time as Clock
from pathlib import Path as FilePath


# the launcher starts an actual descendant before it enters an unreturning wait
def HangCollector(RunPath: FilePath) -> None:
    Child = Subprocess.Popen(
        [System.executable, "-I", "-S", "-c", "import time; time.sleep(120)"]
    )
    _ = (RunPath / "fixture.json").write_text(
        JsonCodec.dumps({"collector": OsLayer.getpid(), "child": Child.pid}),
        encoding="utf-8",
    )
    Clock.sleep(120)


# fixture use of the watcher shares native job creation and drain with the campaign
def WatchFixture(RunPath: FilePath, ResearchPath: str) -> None:
    System.path.insert(0, ResearchPath)
    Watcher = ScriptRun.run_path(str(FilePath(ResearchPath) / "ScopeWatchdog.py"))
    Command = [
        System._base_executable,
        "-I",
        "-S",
        __file__,
        "collect",
        str(RunPath),
    ]
    Receipt = Watcher["watch"](
        Command,
        RunPath,
        dict(OsLayer.environ),
        RunPath,
        8,
        {"scope": "disposable_scope_watch_fixture"},
    )
    assert Receipt["outcome"] == "timed_out" and Receipt["job_drained"] is True, Receipt


if __name__ == "__main__":
    if System.argv[1] == "collect":
        HangCollector(FilePath(System.argv[2]))
    else:
        WatchFixture(FilePath(System.argv[2]), System.argv[3])
