from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from pytest import mark as TestMark


# windows interruption must preserve worker cleanup and its eventual exit status
@TestMark.skipif(KPlatform != "win32", reason="Windows launcher process ownership")
def CheckInterrupt(TmpPath: FilePath) -> None:
    RootPath = TmpPath / "Checkout"
    (RootPath / ".git").mkdir(parents=True)
    (RootPath / "src/convert").mkdir(parents=True)
    ToolPath = RootPath / "re/automation/Controller.py"
    ToolPath.parent.mkdir(parents=True)
    _ = ToolPath.write_text(
        """from pathlib import Path
import sys
import time
Path(sys.argv[1]).write_bytes(b"ready")
try:
    time.sleep(4)
finally:
    Path(sys.argv[2]).write_bytes(b"cleaned")
raise SystemExit(37)
""",
        encoding="utf-8",
    )
    ParentPath = TmpPath / "Launcher.py"
    _ = ParentPath.write_text(
        """import _thread
import sys
import threading
import time
from pathlib import Path
ReadyPath = Path(sys.argv[1])
DonePath = sys.argv[2]
RootPath = sys.argv[3]
def InterruptParent():
    for _ in range(3000):
        if ReadyPath.exists():
            (ReadyPath.parent / "Interrupted").write_bytes(b"sent")
            _thread.interrupt_main()
            return
        time.sleep(0.01)
threading.Thread(target=InterruptParent, daemon=True).start()
sys.argv[:] = ["kit", "research", "--root", RootPath, "controller", str(ReadyPath), DonePath]
from KitCli.MainEntry import MainEntry
raise SystemExit(MainEntry())
""",
        encoding="utf-8",
    )
    DonePath = TmpPath / "Cleaned"
    Result = RunProcess(
        (
            KPythonPath,
            "-I",
            str(ParentPath),
            str(TmpPath / "Ready"),
            str(DonePath),
            str(RootPath),
        ),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert Result.returncode == 37, Result.stderr
    assert DonePath.read_bytes() == b"cleaned"
    assert (TmpPath / "Interrupted").read_bytes() == b"sent"
