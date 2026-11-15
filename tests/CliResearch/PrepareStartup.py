from pathlib import Path as FilePath


# deterministic startup cancellation needs a separate observer around the actual process creation boundary
def PrepareStartup(WorkPath: FilePath) -> FilePath:
    BootstrapPath = WorkPath / "Bootstrap.py"
    _ = BootstrapPath.write_text(
        """from pathlib import Path
import sys
import time

# handoff observation needs stable paths after the developer command replaces its arguments
KRoot, KReady, KDone, KSpawned, KRelease = sys.argv[1:]

# startup cancellation needs a deterministic pause around an actual child process
def PauseSpawn(Frame, Event, Value):
    if (Event == "return" and Frame.f_code.co_name == "__init__"
            and Frame.f_globals.get("__name__") == "subprocess"):
        Child = Frame.f_locals.get("self")
        if getattr(Child, "pid", None) is not None:
            Path(KSpawned).write_text(str(Child.pid))
            for _ in range(3000):
                if Path(KRelease).exists():
                    break
                time.sleep(0.01)
            else:
                raise TimeoutError("startup handoff was not released")
    return PauseSpawn
sys.settrace(PauseSpawn)
from KitCli.MainEntry import MainEntry
sys.argv[:] = ["kit", "research", "--root", KRoot, "controller", KReady, KDone, "handled"]
raise SystemExit(MainEntry())
""",
        encoding="utf-8",
    )
    return BootstrapPath
